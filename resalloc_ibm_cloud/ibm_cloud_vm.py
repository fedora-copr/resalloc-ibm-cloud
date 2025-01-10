"""
Start a new VM in IBM Cloud under the copr-team account.
"""


import logging
import os
import random
import subprocess
import sys
from time import sleep

import requests

from resalloc_ibm_cloud.helpers import get_service
from resalloc_ibm_cloud.argparsers import vm_arg_parser
from resalloc_ibm_cloud.constants import LIMIT


def resalloc_to_ibmcloud_name(name):
    """
    IBM CLoud doesn't like underscores, and non-alphabetical characters at the
    beginning of resource names.
    """
    return name.replace("_", "-")


def bind_floating_ip(service, instance_id, opts):
    """
    Assign an existing Floating IP to given instance.
    """
    if not opts.floating_ip_uuid:
        raise RuntimeError("opts.floating_ip_uuid not selected")

    log = opts.log
    log.info("Bind floating IP %s", opts.floating_ip_uuid)

    network_interface_id = opts.instance_created["primary_network_interface"]["id"]
    log.info("Network interface ID: %s", network_interface_id)
    result = service.add_instance_network_interface_floating_ip(
        instance_id,
        network_interface_id,
        opts.floating_ip_uuid,
    )
    ip_address = result.result["address"]
    log.info("Floating IP: %s", ip_address)
    return ip_address


def allocate_and_assign_ip(service, opts):
    """
    Allocate and assign a Floating IP to an existing machine in one call.
    """
    opts.log.info("Allocating a new temporary Floating IP")
    service_url = f"https://{opts.region}.iaas.cloud.ibm.com/v1"
    url = service_url + "/floating_ips"
    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer " + service.authenticator.token_manager.get_token(),
    }
    params = {
        "version": "2022-01-18",
        "generation": "2",
    }
    data = {
        "name": opts.instance_name,
        "target": {
            "id": opts.instance_created["primary_network_interface"]["id"],
        },
    }
    response = requests.post(url, headers=headers, json=data, params=params)
    assert response.status_code == 201
    opts.allocated_floating_ip_id = response.json()["id"]
    return response.json()["address"]


def run_playbook(host, opts):
    """
    Run ansible-playbook against the given hostname
    """
    cmd = ["ansible-playbook", opts.playbook, "--inventory", f"{host},"]
    subprocess.check_call(cmd, stdout=sys.stderr, stdin=subprocess.DEVNULL)


def get_zone_and_subnet_id(opts):
    """
    From command-line opts, assign opts.zone and opts.subnet_id.
    The zone (lab/location) must be a valid choice within --region.
    """
    random_subnet = random.choice(opts.subnets_ids)
    opts.zone, opts.subnet_id = random_subnet.split(":")


def _get_private_ip_of_instance(instance_id, service):
    for _ in range(5):
        private_ip = service.get_instance(
            instance_id
        ).get_result()["primary_network_interface"]["primary_ip"]["address"]
        if private_ip != "0.0.0.0":
            return private_ip

        sleep(5)

    raise TimeoutError("Instance creation took too much time")


def check_field_len(log, config, itemspec, max_length):
    """
    Check that CONFIG dict (sub-)item specified by ITEMSPEC (list of hashable
    objects determining the location in the dict) has length <= MAX_LENGTH.
    """
    to_check = config
    for i in itemspec:
        to_check = to_check[i]
    if len(to_check) <= max_length:
        return
    log.error("Field %s is longer than %s characters: %s",
              ".".join(itemspec), max_length, to_check)
    sys.exit(1)


def create_instance(service, instance_name, opts):
    """
    Start the VM, name it "instance_name"
    """

    log = opts.log

    instance_prototype_model = {
        "keys": [{"id": opts.ssh_key_id}],
        "name": instance_name,
        "profile": {"name": opts.instance_type},
        "vpc": {
            "id": opts.vpc_id,
        },
        "boot_volume_attachment": {
            "volume": {
                "name": instance_name + "-root",
                "profile": {
                    "name": "general-purpose",
                },
            },
            "delete_volume_on_instance_delete": True,
        },
        "image": {"id": opts.image_uuid},
        "primary_network_interface": {
            "name": "primary-network-interface",
            "subnet": {
                "id": opts.subnet_id,
            },
            "security_groups": [
                {"id": opts.security_group_id},
            ],
        },
        "zone": {
            "name": opts.zone,
        },
        "volume_attachments": [
            {
                "volume": {
                    "name": instance_name + "-swap",
                    "capacity": opts.additional_volume_size,
                    "profile": {"name": "general-purpose"},
                },
                "delete_volume_on_instance_delete": True,
            }
        ],
    }

    if opts.resource_group_id:
        instance_prototype_model["resource_group"] = {"id": opts.resource_group_id}

    for items in [
        ["name"],
        ["boot_volume_attachment", "volume", "name"],
        ["volume_attachments", 0, "volume", "name"],
    ]:
        check_field_len(log, instance_prototype_model, items, 63)

    ip_address = None
    instance_created = None
    opts.allocated_floating_ip_id = None
    try:
        response = service.create_instance(instance_prototype_model)
        instance_created = instance_name
        opts.instance_created = response.get_result()
        log.debug("Instance response: %s", response)
        log.debug("Instance response[result]: %s", opts.instance_created)
        instance_id = opts.instance_created["id"]
        log.info("Instance ID: %s", instance_id)

        if opts.tags:
            assign_user_tags(opts.instance_created["crn"], service, opts)

        if opts.no_floating_ip:
            # assuming you have access through to private IP address
            ip_address = _get_private_ip_of_instance(instance_id, service)
        elif opts.floating_ip_uuid:
            ip_address = bind_floating_ip(service, instance_id, opts)
        else:
            ip_address = allocate_and_assign_ip(service, opts)

        _wait_for_ssh(ip_address)
        run_playbook(ip_address, opts)
        # Tell the Resalloc clients how to connect to this instance.
        print(ip_address)
    except:
        if instance_created:
            log.info("Removing the failed machine")
            delete_instance(service, instance_name, opts)
        raise


def assign_user_tags(crn, service, opts):
    """
    Assign tags to the resource according to the CRN within the region.
    """
    service_url = "https://tags.global-search-tagging.cloud.ibm.com/v3"
    url = service_url + "/tags/attach?tag_type=user"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {service.authenticator.token_manager.get_token()}",
        "Content-Type": "application/json",
    }
    data = {
        "resources": [{"resource_id": crn}],
        "tag_names": list(opts.tags),
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()


def delete_all_ips(service):
    """
    Go through all reserved IPs, and remove all which are not assigned
    to any VM
    """
    response_list = service.list_floating_ips().get_result()["floating_ips"]
    for fip in response_list:
        if fip["status"] != "available":
            continue
        service.delete_floating_ip(fip["id"])


def delete_instance(service, instance_name, opts):
    """
    Repeatedly try to remove the instance, to minimize the chances for
    leftovers.
    """
    for _ in range(5):
        try:
            delete_instance_attempt(service, instance_name, opts)
            break
        except RuntimeError:
            opts.log.exception("Attempt to delete instance failed")


def delete_instance_attempt(service, instance_name, opts):
    """one attempt to delete instance by it's name"""
    log = opts.log
    log.info("Deleting instance %s", instance_name)

    delete_instance_id = None
    response_list = service.list_instances().get_result()["instances"]
    for item in response_list:
        log.debug("Available: %s %s %s", item["id"], item["name"], item["status"])
        if instance_name == item["name"]:
            delete_instance_id = item["id"]

    floating_ip_id = None
    response_list = service.list_floating_ips().get_result()["floating_ips"]
    for floating_ip in response_list:
        if floating_ip["name"].startswith(instance_name):
            floating_ip_id = floating_ip["id"]

    if delete_instance_id:
        resp = service.delete_instance(delete_instance_id)
        assert resp.status_code == 204
        log.debug("Delete instance request delivered")

    if floating_ip_id:
        resp = service.delete_floating_ip(floating_ip_id)
        assert resp.status_code == 204
        log.debug("Delete IP request delivered")

    # Query all volumes only after already potentially deleting an instance.
    # The volumes should already be deleted automatically.
    volume_ids = []
    volumes = service.list_volumes(limit=LIMIT).result["volumes"]
    for volume in volumes:
        if not volume["name"].startswith(instance_name):
            continue

        if volume.get('attachment_state') == 'attached':
            # Error 409 - can't remove attached volumes
            continue

        # Otherwise Error: Delete volume failed. Volume can be deleted
        # only when its status is available or failed., Code: 409
        if not volume["status"] in ["available", "failed"]:
            continue

        log.info("Volume '%s' (%s) is %s, removing manually", volume["name"],
                 volume["id"], volume["status"])
        volume_ids.append(volume["id"])

    if volume_ids:
        for volume_id in volume_ids:
            log.info("Deleting volume %s (%s)", volume_id)
            resp = service.delete_volume(volume_id)
            assert resp.status_code == 204
            log.debug("Delete volume request delivered")


def _wait_for_ssh(floating_ip):
    cmd = [
        "resalloc-wait-for-ssh",
        "--log",
        "debug",
        "--timeout",
        "240",
        floating_ip,
    ]
    subprocess.check_call(cmd, stdout=sys.stderr)


def detect_floating_ip_uuid(service, opts):
    """
    Depending on options, decide what floating IP uuid to use.
    """
    log = opts.log

    if opts.floating_ip_uuid:
        # the IP id is known
        log.info("Using pre-selected Floating IP address %s",
                 opts.floating_ip_uuid)
        return

    if opts.floating_ip_name:
        log.info("Mapping Floating IP name to UUID")
        response_list = service.list_floating_ips().get_result()["floating_ips"]
        floating_ip_uuid = None
        for item in response_list:
            if item["name"] != opts.floating_ip_name:
                continue
            if item["status"] != "available":
                raise RuntimeError(f"Floating IP {opts.floating_ip_name} is used")
            floating_ip_uuid = item["id"]

        if floating_ip_uuid is None:
            raise RuntimeError(f"UUID for Floating IP {opts.floating_ip_name} "
                               "not found")

    if opts.floating_ip_per_subnet_map:
        id_in_pool = int(os.environ.get("RESALLOC_ID_IN_POOL", -1))
        if id_in_pool == -1:
            raise RuntimeError("--floating-ip-uuid-in-pool requires "
                               "$RESALLOC_ID_IN_POOL var in environment")

        opts.floating_ip_uuid = opts.floating_ip_per_subnet_map[opts.subnet_id][id_in_pool]
        log.info("Selected %s-th Floating IP UUID: %s", id_in_pool,
                 opts.floating_ip_uuid)
        return


def prepare_opts_floating_ip_uuid_map(opts):
    """
    Construct opts.floating_ip_uuid_in_subnet map from
    opts.floating_ip_uuid_in_subnet.
    """
    opts.floating_ip_per_subnet_map = {}
    if opts.floating_ip_uuid_in_subnet:
        for subnet_id, ip_id in opts.floating_ip_uuid_in_subnet:
            if subnet_id not in opts.floating_ip_per_subnet_map:
                opts.floating_ip_per_subnet_map[subnet_id] = []
            opts.floating_ip_per_subnet_map[subnet_id].append(ip_id)


def main():
    """Entrypoint to the script."""

    opts = vm_arg_parser().parse_args()

    log_level = getattr(logging, opts.log_level.upper())
    logging.basicConfig(format="%(levelname)s: %(message)s", level=log_level)
    log = logging.getLogger()
    opts.log = log

    service = get_service(opts)

    if hasattr(opts, "name"):
        name = resalloc_to_ibmcloud_name(opts.name)
        opts.instance_name = name
        opts.instance = "production" if "-prod-" in name else "devel"

    if opts.subparser == "create":
        # Perform these steps *before* starting the machine allocation.  These
        # methods performs some offline checks and may also query the cloud
        # (generating additional API traffic).  These checks could result in
        # various failures, and if that happens, the instance allocation would
        # have been unnecessary (triggering subsequent deallocation).
        # construct a subnet_id → list_of_ips map for later convenience
        prepare_opts_floating_ip_uuid_map(opts)
        get_zone_and_subnet_id(opts)
        detect_floating_ip_uuid(service, opts)
        # High chance the machine will start fine, let's try now.
        create_instance(service, name, opts)
    elif opts.subparser == "delete":
        delete_instance(service, name, opts)
    elif opts.subparser == "delete-free-floating-ips":
        delete_all_ips(service)

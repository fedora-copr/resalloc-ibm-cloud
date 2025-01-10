"""
ArgumentParser getters on one place, this simplifies generating manual pages.
"""

import argparse
import sys

if 313 > sys.version_info.major * 100 + sys.version_info.minor:
    DEPRECATED_OPTION = {}
else:
    DEPRECATED_OPTION = {"deprecated": True}


def _pfx(name):
    return "resalloc-ibm-cloud-" + name


def _default_arg_parser(prog=None):
    """
    The part that every resalloc-ibm-cloud utility needs
    """

    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument(
        "--token-file", help="Path to IBM cloud token file", required=True
    )
    parser.add_argument(
        "--zone",
        help="default IBM Cloud zone. e.g. jp-tok, us-east, us-west, ...",
        dest="region",
        **DEPRECATED_OPTION,
    )
    parser.add_argument(
        "--region",
        help="default IBM Cloud zone. e.g. jp-tok, us-east, us-west, ...",
    )
    return parser


def vm_arg_parser():
    """
    Parser for the resalloc-ibm-cloud-vm utility.
    """
    parser = _default_arg_parser(prog=_pfx("vm"))
    parser.add_argument("--log-level", default="info")

    subparsers = parser.add_subparsers(dest="subparser")
    subparsers.required = True
    parser_create = subparsers.add_parser(
        "create", help="Create an instance in IBM Cloud"
    )
    parser_create.add_argument("name")
    parser_create.add_argument("--playbook", help="Path to playbook", required=True)
    parser_create.add_argument("--image-uuid", required=True)
    parser_create.add_argument("--vpc-id", required=True)
    parser_create.add_argument("--security-group-id", required=True)
    parser_create.add_argument("--ssh-key-id", required=True)
    parser_create.add_argument("--instance-type", help="e.g. cz2-2x4", required=True)

    f_ip_group = parser_create.add_mutually_exclusive_group()

    f_ip_group.add_argument("--floating-ip-name", default=None)
    f_ip_group.add_argument("--floating-ip-uuid", default=None)
    f_ip_group.add_argument(
        "--no-floating-ip", action="store_true", help="Don't use floating IPs (for VPN)"
    )
    f_ip_group.add_argument("--floating-ip-uuid-in-subnet", nargs=2,
                            metavar=("SUBNET-ID", "FLOATING-IP-UUID"),
                            action='append', help=(
        "Add a Floating IP UUID into the list of IPs that can be used for the "
        "corresponding subnet ID.  Depending on the $RESALLOC_ID_IN_POOL (given "
        "by Resalloc server) the script assigns the newly started machine "
        "n-th IP from the list."
    ))
    parser_create.add_argument(
        "--subnets-ids",
        type=str,
        nargs="+",
        help=(
            "Space separated list of ZONE:SUBNET_ID pairs.  The ZONE "
            "must be a valid ZONE ID within the specified --region ("
            "e.g., 'eu-es-2' within 'eu-es' region)."
        ),
        required=True,
    )
    parser_create.add_argument(
        "--additional-volume-size",
        type=int,
        help="Allocate additional volume of given size in GB",
        default=160,
    )
    parser_create.add_argument(
        "--resource-group-id", help="Resource group id, get it from `$ ibmcloud resources`"
    )
    parser_create.add_argument(
        "--tags",
        type=str,
        nargs="+",
        help="Space separated list of key:value tags, e.g. app:copr",
    )
    parser_delete = subparsers.add_parser(
        "delete", help="Delete instance by it's name from IBM Cloud"
    )
    parser_delete.add_argument("name")
    subparsers.add_parser(
        "delete-free-floating-ips", help="Clean all IPs without an assigned VM"
    )
    return parser


def _list_arg_parser(prog=None):
    """
    Parser for listing utilities
    """
    parser = _default_arg_parser(prog=prog)
    parser.add_argument("--pool")
    return parser

def list_deleting_vms_parser():
    """ parser for listing vms """
    return _list_arg_parser(prog=_pfx("list-deleting-vms"))

def list_vms_parser():
    """ parser for listing deleting vms """
    return _list_arg_parser(prog=_pfx("list-vms"))

def list_deleting_volumes_parser():
    """ parser for listing vms """
    return _default_arg_parser(prog=_pfx("list-deleting-volumes"))

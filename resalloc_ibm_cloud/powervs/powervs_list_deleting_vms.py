"""
List all IBM Cloud PowerVS instances that are in deleting-like state.
"""

from resalloc_ibm_cloud.powervs.credentials import get_powervs_credentials
from resalloc_ibm_cloud.powervs.client import PowerVSClient
from resalloc_ibm_cloud.argparsers import powervs_list_deleting_vms_parser


def list_deleting_vms(client: PowerVSClient):
    """
    List all PowerVS instances that are in a deleting-like state.

    Args:
        client: PowerVS client
    """
    for instance in client.list_instances():
        # check if the instance is being deleted
        # PowerVS instances can have states like: SHUTTING-DOWN, DELETING
        status = instance.get("status", "").upper()
        if "DELET" in status or "SHUTTING" in status:
            print(
                f"{instance['pvmInstanceID']} {instance.get('serverName', 'unknown')}"
            )


def main():
    """Entrypoint to the script."""
    opts = powervs_list_deleting_vms_parser().parse_args()

    credentials = get_powervs_credentials(opts.token_file, opts.crn)
    client = PowerVSClient(credentials)

    list_deleting_vms(client)

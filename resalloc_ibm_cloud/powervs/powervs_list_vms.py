"""
List all IBM Cloud PowerVS instances.
"""

import os
import sys

from resalloc_ibm_cloud.powervs.credentials import get_powervs_credentials
from resalloc_ibm_cloud.powervs.client import PowerVSClient
from resalloc_ibm_cloud.argparsers import powervs_list_vms_parser


def list_vms(client: PowerVSClient, pool_id: str) -> set[str]:
    """
    List all PowerVS instances for the specified pool.

    Args:
        client: PowerVS client
        pool_id: Pool ID prefix to filter instances

    Returns:
        Set of resource names that match the pool ID
    """
    resources = set()

    for instance in client.list_instances():
        name = instance.get("serverName", "")
        if name.startswith(pool_id):
            resources.add(name)

    return resources


def main():
    """Entrypoint to the script."""
    opts = powervs_list_vms_parser().parse_args()

    pool_id = opts.pool or os.getenv("RESALLOC_POOL_ID")
    if not pool_id:
        sys.stderr.write("Specify pool ID by --pool or $RESALLOC_POOL_ID\n")
        sys.exit(1)

    credentials = get_powervs_credentials(opts.token_file, opts.crn)
    client = PowerVSClient(credentials)

    resources = list_vms(client, pool_id)

    for name in resources:
        print(name)

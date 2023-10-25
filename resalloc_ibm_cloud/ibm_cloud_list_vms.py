"""
List all IBM Cloud instances.
"""

import os
import sys

from resalloc_ibm_cloud.helpers import get_service
from resalloc_ibm_cloud.argparsers import list_vms_parser
from resalloc_ibm_cloud.constants import LIMIT


def main():
    """An entrypoint to the script."""

    opts = list_vms_parser().parse_args()

    pool_id = opts.pool or os.getenv("RESALLOC_POOL_ID")
    if not pool_id:
        sys.stderr.write("Specify pool ID by --pool or $RESALLOC_POOL_ID\n")
        sys.exit(1)

    service = get_service(opts)

    # Gather the list of all resources here
    resources = set()
    instances = service.list_instances(limit=LIMIT).result["instances"]
    for server in instances:
        # Resalloc works with underscores, which is not allowed in IBM Cloud
        name = server["name"].replace("-", "_")
        if name.startswith(pool_id):
            resources.add(name)

    volumes = service.list_volumes(limit=LIMIT).result["volumes"]
    for volume in volumes:
        # Resalloc works with underscores, which is not allowed in IBM Cloud
        name = volume["name"].replace("-", "_")
        if name.startswith(pool_id):
            name = name.rsplit("_", 1)[0]
            resources.add(name)

    f_ips = service.list_floating_ips().get_result()["floating_ips"]
    for f_ip in f_ips:
        name = f_ip["name"].replace("-", "_")
        if name.startswith(pool_id):
            resources.add(name)

    # Print them out, so upper level tooling can work with the list
    for name in resources:
        # The only stdout output comes here!
        print(name)

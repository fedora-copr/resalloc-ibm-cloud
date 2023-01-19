"""
List all IBM Cloud instances.
"""

import os
import sys

from resalloc_ibm_cloud.helpers import default_arg_parser, get_service
from resalloc_ibm_cloud.constants import LIMIT


def _get_arg_parser():
    parser = default_arg_parser()
    parser.add_argument("--pool")
    return parser


def main():
    """An entrypoint to the script."""

    opts = _get_arg_parser().parse_args()

    pool_id = opts.pool or os.getenv("RESALLOC_POOL_ID")
    if not pool_id:
        sys.stderr.write("Specify pool ID by --pool or $RESALLOC_POOL_ID\n")
        sys.exit(1)

    cmd = f"source {opts.token_file} ; echo $IBMCLOUD_API_KEY"
    service = get_service(cmd, opts)

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

    # Print them out, so upper level tooling can work with the list
    for name in resources:
        # The only stdout output comes here!
        print(name)

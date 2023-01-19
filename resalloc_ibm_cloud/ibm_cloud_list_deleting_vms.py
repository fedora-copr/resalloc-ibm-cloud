"""
List all IBM Cloud instances that are in Deleting state
"""

import sys

from resalloc_ibm_cloud.helpers import default_arg_parser, get_service
from resalloc_ibm_cloud.constants import LIMIT


def _get_arg_parser():
    parser = default_arg_parser()
    return parser


def main():
    opts = _get_arg_parser().parse_args()
    cmd = f"source {opts.token_file} ; echo $IBMCLOUD_API_KEY"
    service = get_service(cmd, opts)

    instances = service.list_instances(limit=LIMIT).result["instances"]
    for server in instances:
        # Resalloc works with underscores, which is not allowed in IBM Cloud
        if server["status"] == "deleting":
            print("{} {}".format(server["id"], server["name"]))

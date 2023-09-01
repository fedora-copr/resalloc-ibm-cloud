"""
ArgumentParser getters on one place, this simplifies generating manual pages.
"""

import argparse

def default_arg_parser():
    """
    The part that every resalloc-ibm-cloud utility needs
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--token-file", help="Path to IBM cloud token file", required=True
    )
    parser.add_argument(
        "--service-url",
        help="SERVICE URL e.g. https://jp-tok.iaas.cloud.ibm.com/v1",
        required=True,
    )
    return parser


def vm_arg_parser():
    """
    Parser for the resalloc-ibm-cloud-vm utility.
    """
    parser = default_arg_parser()
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
    parser_create.add_argument("--floating-ip-name", default=None)
    parser_create.add_argument(
        "--zones",
        help=(
            "Path to json file with zones as keys and subnet id as value."
            'content of file will look like: {"jp-tok-1": "secret-subnet-id-123-abcd", ...}'
        ),
        required=True,
    )
    parser_delete = subparsers.add_parser(
        "delete", help="Delete instance by it's name from IBM Cloud"
    )
    parser_delete.add_argument("name")
    subparsers.add_parser(
        "delete-free-floating-ips", help="Clean all IPs without an assigned VM"
    )
    return parser


def vm_list_arg_parser():
    """
    Parser for the resalloc-ibm-cloud-list-vms utility.
    """
    parser = default_arg_parser()
    parser.add_argument("--pool")
    return parser

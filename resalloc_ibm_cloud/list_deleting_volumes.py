"""
List all IBM Cloud volumes that are in Deleting state.  This helps with
support-case reporting to IBM folks.
"""

from resalloc_ibm_cloud.helpers import get_service
from resalloc_ibm_cloud.argparsers import list_deleting_volumes_parser
from resalloc_ibm_cloud.constants import LIMIT


def main():
    """
    Print ID:name pairs.
    """

    opts = list_deleting_volumes_parser().parse_args()
    # TODO: fix get_service
    cmd = f"source {opts.token_file} ; echo $IBMCLOUD_API_KEY"
    service = get_service(cmd, opts)

    volumes = service.list_volumes(limit=LIMIT).result["volumes"]
    for volume in volumes:
        if volume["status"] in ["available"]:
            continue
        print(f"{volume['id']} (name={volume['name']}) -> {volume['status']}")

if __name__ == "__main__":
    main()

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
    service = get_service(opts)
    volumes = service.list_volumes(limit=LIMIT).result["volumes"]
    for volume in volumes:
        if volume["status"] in ["available"]:
            continue
        print(f"{volume['id']} (name={volume['name']}) -> {volume['status']}")

if __name__ == "__main__":
    main()

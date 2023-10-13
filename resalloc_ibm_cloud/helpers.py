import subprocess
import datetime
from argparse import Namespace

from ibm_vpc import VpcV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator


def get_service(opts: Namespace):
    """
    Taking command-line argument options, load the IBM Cloud token file and
    perform authentication against given IBM Cloud end-point.  We expect that
    the token file is a shell file that defines $IBMCLOUD_API_KEY variable
    inside.  Use techniques like:

        echo -n "Please enter your IBM Cloud key: "
        read -sr IBMCLOUD_API_KEY
        echo

    Input options:
        opts.token_file -> file to read and process with shell
        opts.zone       -> zone in IBM Cloud, e.g. 'jp-tok'
    """

    cmd = f"source {opts.token_file} ; echo $IBMCLOUD_API_KEY"
    output = subprocess.check_output(cmd, shell=True)
    token = output.decode("utf-8").strip().rsplit("\n", maxsplit=1)[-1]
    authenticator = IAMAuthenticator(token)
    now = datetime.datetime.now()
    service = VpcV1(now.strftime("%Y-%m-%d"), authenticator=authenticator)
    service.set_service_url(f"https://{opts.zone}.iaas.cloud.ibm.com/v1")
    return service

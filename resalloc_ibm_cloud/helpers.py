import subprocess
import datetime
from argparse import Namespace

from ibm_vpc import VpcV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator


def get_service(cmd: str, opts: Namespace):
    output = subprocess.check_output(cmd, shell=True)
    token = output.decode("utf-8").strip().rsplit("\n", maxsplit=1)[-1]
    authenticator = IAMAuthenticator(token)
    now = datetime.datetime.now()
    service = VpcV1(now.strftime("%Y-%m-%d"), authenticator=authenticator)
    service.set_service_url(f"https://{opts.zone}.iaas.cloud.ibm.com/v1")
    return service

import sys
from typing import Optional, Tuple
from spotinst_kubernetes_cluster_autoscaler.configure import *


def main_logic_flow():
    """
        Will decide on the proper way to connect to the kubernetes API (via API request, as declered on kubeconfig file or
        via using in cluster configuration based on what the user pass, priority is api>kubeconfig>in_cluster

    Exceptions:
        :except FileNotFoundError: will return HTTP 404 with a JSON of the stderr it catch from "terraform init" or
        "terraform apply"
    """
    try:
        pass
        # read configuration
        configuration = read_configurations(os.getenv("CONFIG_DIR", "config"))
        # check connection to cluster works
        # check current cluster CPU usage
        # check current cluster memory usage
        # check current pod deployment status
        # run logic to see if needs scaling up
        # if needed scale up
        # if not run logic to see if needed to scale down
        # if needed scale down
    except Exception as e:
        print("failed main logic flow - exiting")
        print(e, file=sys.stderr)
        exit(2)

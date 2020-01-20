import sys
from typing import Optional, Tuple
from spotinst_kubernetes_cluster_autoscaler.configure import *


def main_logic_flow():
    """
        The main logic process, first read the configuration options, then get the current cluster CPU, Memory usage &
        check if there are any pod deployments waiting for resources, then pass those params to the logic which decides
        if it needs to scale up or down and then scale the spotinst elastigroup if needed before exiting
    """
    try:
        print("Starting spotinst_kubernetes_cluster_autoscaler")
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

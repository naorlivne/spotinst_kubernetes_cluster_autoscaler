import sys
from typing import Optional, Tuple
from spotinst_kubernetes_cluster_autoscaler.configure import *


def main_logic_flow():
    """
        Will decide on the proper way to connect to the kubernetes API (via API request, as declered on kubeconfig file or
        via using in cluster configuration based on what the user pass, priority is api>kubeconfig>in_cluster

        Arguments:
            :param connection_config: the configuration dict which all configuration of possible kubernetes connections are
            located in

        Returns:
            :return kube_connection_method: one of: "api", "kube_config" or "in_cluster"
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

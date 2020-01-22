from kubernetes import client, config
from typing import Optional
import sys


class KubeGetScaleData:
    """
       This class does everything related to kubernetes, this includes figuring out the current number of nodes that
       are connected to the cluster, if there's any containers stuck in a pending state due to lack of resources and the
       memory & CPU resource usage
    """

    def __init__(self, connection_method: str,  api_endpoint: str = Optional[str], context_name: Optional[str] = None,
                 token: Optional[str] = None, kubeconfig_path: Optional[str] = None):
        """
           Init the kubernetes connection while auto figure out the best connection auth method

           Arguments:
               :param connection_method: how to connect to the cluster, options are "api", "kube_config" or "in_cluster"
               :param api_endpoint: the API endpoint of the kubernetes cluster to work against if not connecting via a
               kubeconfig file or from inside the cluster
               :param context_name: the name of the context inside the kubeconfig to use if "kube_config" is used
               :param token: if connecting via "api" the bearer token to auth with
               :param kubeconfig_path: if using kubeconfig the path to the kubeconfig file

            Raises:
                :raise ValueError: if passing a connection_method that isn't on the list of choices
        """
        if connection_method == "in_cluster":
            print("connecting via in_cluster method")
            config.load_incluster_config()
        elif connection_method == "kube_config":
            print("connecting via kube_config method")
            config.load_kube_config(context=context_name, config_file=kubeconfig_path)
        elif connection_method == "api":
            print("connecting via api method")
            kube_config_object = client.Configuration()
            kube_config_object.host = api_endpoint
            kube_config_object.verify_ssl = False
            kube_config_object.api_key = {"authorization": "Bearer " + token}
            self.kube_client = client.ApiClient(kube_config_object)
            self.v1 = client.CoreV1Api(self.kube_client)
            self.custom_object_api = client.CustomObjectsApi(api_client=self.kube_client)
        else:
            print("valid connection method to kubernetes must be one of 'api', 'kube_config' or 'in_cluster'",
                  file=sys.stderr)
            raise ValueError

        # both the "in_cluster" & "kube_config" options use the same config, only the "api" method is different so
        # running both at the same block to keep DRY, "api" gets configured above to avoid needing another elif that
        # would be redundant otherwise
        if connection_method != "api":
            self.kube_client = client
            self.v1 = self.kube_client.CoreV1Api()
            self.custom_object_api = self.kube_client.CustomObjectsApi()

    def get_cpu_usage(self):
        """
            Get the current number of spotinst nodes

            Returns:
                :return current number of nodes in the elastigroup
        """
        pass

    def get_mem_usage(self):
        """
            Get the current number of spotinst nodes

            Returns:
                :return current number of nodes in the elastigroup
        """
        pass

    def pod_stuck_exist(self):
        """
            Get the current number of spotinst nodes for all namespaces

            Returns:
                :return current number of nodes in the elastigroup
        """
        pass

    def get_connected_nodes_count(self):
        """
            Get the current number of spotinst nodes

            Returns:
                :return current number of nodes in the elastigroup
        """
        pass

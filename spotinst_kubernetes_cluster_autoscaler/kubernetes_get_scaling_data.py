from kubernetes import client, config
from typing import Optional
import sys
import time


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

    def get_cpu_usage(self) -> int:
        """
            Get the CPU usage percentage of the cluster

            Returns:
                :return current CPU usage percentage of the cluster
        """
        pass

    def get_mem_usage(self) -> int:
        """
            Get the memory usage percentage of the cluster

            Returns:
                :return current memory usage percentage of the cluster
        """
        pass

    def get_number_of_pending_pods(self) -> int:
        """
            Get the number of pods that are stuck pending

            Returns:
                :return current number of pods stuck pending
        """
        pod_list = self.v1.list_pod_for_all_namespaces(watch=False, field_selector="status.phase=Pending",
                                                       timeout_seconds=10)
        return pod_list.items.__len__()

    def pending_pods_exist(self, seconds_to_wait_between_checks: int = 5) -> bool:
        """
            Check if there's a pod that cant start do to not having enough resources to be placed and only alert if
            there are pods that are stuck waiting longer then seconds_to_wait_between_checks

            Returns:
                :return True if there are pods stuck waiting longer then seconds_to_wait_between_checks, False otherwise
        """
        pending_pods = False
        if self.get_number_of_pending_pods() > 0:
            time.sleep(seconds_to_wait_between_checks)
            if self.get_number_of_pending_pods() > 0:
                pending_pods = True
        return pending_pods

    def get_connected_nodes_count(self) -> int:
        """
            Get the current number of nodes connected to the kubernetes cluster

            Returns:
                :return current number of nodes in the elastigroup
        """
        nodes_list = self.v1.list_node()
        return nodes_list.items.__len__()

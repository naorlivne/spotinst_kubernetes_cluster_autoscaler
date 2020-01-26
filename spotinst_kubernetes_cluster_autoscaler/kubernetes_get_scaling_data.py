from kubernetes import client, config
from typing import Optional, Tuple
import sys
import time
from si_prefix import si_parse


def unit_converter(unit_added_string: str) -> float:
    """
        convert unit formatted strings to floating numbers without any units

        Arguments:
            :param unit_added_string: the unit added number we want to convert to be unit free

        Returns::
            :return unit_in_float: the same number but in float without the units

        Raises::
            :raise TypeError: if trying to parse an unknown unit type
            """
    custom_unit_ratio = {
        "Ki": 1024,
        "Mi": 1024 * 1024,
        "Gi": 1024 * 1024 * 1024
    }
    try:
        unit_in_float = float(si_parse(unit_added_string))
    except AttributeError:
        if unit_added_string[-2:] in custom_unit_ratio:
            unit_in_float = float(unit_added_string[:-2]) * custom_unit_ratio[unit_added_string[-2:]]
        else:
            raise TypeError

    return unit_in_float


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

    def get_cpu_and_mem_usage(self) -> Tuple[int, int]:
        """
            Get the CPU & memory usage percentage of the cluster

            Returns:
                :return used_cpu_percentage: CPU usage percentage of the cluster
                :return used_memory_percentage: memory usage percentage of the cluster
        """

        allocatable_cpu = 0
        allocatable_memory = 0
        used_cpu = 0
        used_memory = 0
        requested_cpu = 0
        requests_memory = 0

        nodes_list = self.v1.list_node()
        for node in nodes_list.items:
            allocatable_cpu += unit_converter(node.status.allocatable['cpu'])
            allocatable_memory += unit_converter(node.status.allocatable['memory'])

        pod_list = self.v1.list_pod_for_all_namespaces(watch=False, field_selector="status.phase=Running",
                                                       timeout_seconds=10)
        for pod in pod_list.items:
            for container in pod.spec.containers:
                if (container.resources.requests is not None) and ("cpu" in container.resources.requests):
                    requested_cpu += unit_converter(container.resources.requests['cpu'])
                if (container.resources.requests is not None) and ("memory" in container.resources.requests):
                    requests_memory += unit_converter(container.resources.requests['memory'])

        current_used_metrics = self.custom_object_api.list_cluster_custom_object('metrics.k8s.io', 'v1beta1', 'nodes')
        for node in current_used_metrics['items']:
            used_cpu += unit_converter(node['usage']['cpu'])
            used_memory += unit_converter(node['usage']['memory'])

        max_used_requested_cpu = max([used_cpu, requested_cpu])
        max_used_requested_memory = max([used_memory, requests_memory])

        used_cpu_percentage = int(max_used_requested_cpu / allocatable_cpu * 100)
        used_memory_percentage = int(max_used_requested_memory / allocatable_memory * 100)

        return used_cpu_percentage, used_memory_percentage

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

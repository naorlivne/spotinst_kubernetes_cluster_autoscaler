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


def check_pod_node_affinity(pod) -> dict:
    """
        Check what node affinity & nodeselector is required for the pod to run on, note this is only required per
        run and not preferred and that it will prioritize nodeselector over node affinity in the response and will
        only use the first label (sorry no complex affinity support)

        Arguments:
            :param pod: the pod object to check the affinity of

        Returns:
            :return a dict of the label key:value the pods has a required/nodeselector affinity to
    """
    try:
        if pod.spec.node_selector != {} and pod.spec.affinity.node_affinity is None:
            response = pod.spec.node_selector
        else:
            response = {
                pod.spec.affinity.node_affinity.required_during_scheduling_ignored_during_execution.
                node_selector_terms[0].match_expressions[0].key: pod.spec.affinity.node_affinity.
                required_during_scheduling_ignored_during_execution.node_selector_terms[0].match_expressions[0].
                values[0]
            }
    except AttributeError:
        response = {}
    return response


class KubeGetScaleData:
    """
       This class does everything related to kubernetes, this includes figuring out the current number of nodes that
       are connected to the cluster, if there's any containers stuck in a pending state due to lack of resources and the
       memory & CPU resource usage
    """

    def __init__(self, connection_method: str, api_endpoint: str = Optional[str], context_name: Optional[str] = None,
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

    def get_cpu_and_mem_usage(self, node_selector_label: Optional[str] = None) -> Tuple[int, int]:
        """
            Get the CPU & memory usage percentage of the cluster by figuring out the highest of the requested CPU & mem
            of all containers running in the cluster (or only a portion of the cluster that matches the
            "node_selector_label"& the actually used CPU & mem then dividing that by the total CPU & mem available at
            the kubernetes cluster

            Arguments:
               :param node_selector_label: Optional label to use to filter the nodes to get the usage from only a subset
               of nodes that matches that label, defaults to all nodes, should be a string in the format of "key=value"
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

        nodes_list = self.v1.list_node(label_selector=node_selector_label)
        for node in nodes_list.items:
            allocatable_cpu += unit_converter(node.status.allocatable['cpu'])
            allocatable_memory += unit_converter(node.status.allocatable['memory'])

        if node_selector_label is None:
            pod_list = self.v1.list_pod_for_all_namespaces(watch=False, field_selector="status.phase=Running",
                                                           timeout_seconds=10)
            pod_list_items = pod_list.items
        else:
            pod_list_items = []
            for node in nodes_list.items:
                pod_list = self.v1.list_pod_for_all_namespaces(watch=False, timeout_seconds=10,
                                                               field_selector="status.phase=Running,spec.nodeName=" +
                                                                              str(node.metadata.name))
                pod_list_items += pod_list.items

        for pod in pod_list_items:
            for container in pod.spec.containers:
                if (container.resources.requests is not None) and ("cpu" in container.resources.requests):
                    requested_cpu += unit_converter(container.resources.requests['cpu'])
                if (container.resources.requests is not None) and ("memory" in container.resources.requests):
                    requests_memory += unit_converter(container.resources.requests['memory'])

        current_used_metrics = self.custom_object_api.list_cluster_custom_object('metrics.k8s.io', 'v1beta1', 'nodes')
        for metric_node in current_used_metrics['items']:
            used_cpu += unit_converter(metric_node['usage']['cpu'])
            used_memory += unit_converter(metric_node['usage']['memory'])

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
        pending_pod_list = self.v1.list_pod_for_all_namespaces(watch=False, field_selector="status.phase=Pending",
                                                               timeout_seconds=10)
        return pending_pod_list.items.__len__()

    def pending_pods_exist(self, seconds_to_wait_between_checks: int = 5) -> bool:
        """
            Check if there's a pod that cant start do to not having enough resources to be placed and only alert if
            there are pods that are stuck waiting longer then seconds_to_wait_between_checks

            Arguments:
                :param seconds_to_wait_between_checks: the number of seconds to wait to recheck if the pods are still
                in a pending state

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

    def check_node_group_labels(self, node_selector_label: str = None) -> dict:
        """
            Check what labels are in the "node group", this is done by taking the first server with a matching
            node_selector_label and seeing what labels are on it with the logic behind it being that all nodes in the
            node group will have the same "static" labels and you wouldn't assign pods to nodes based on dynamic labels
            anyway

            Arguments:
                :param node_selector_label: optional label to use to filter the nodes to get the usage from only a
                subset of nodes that matches that label, defaults to all nodes, should be a string in the format of
                "key=value"
            Returns:
                :return a dict of all labels that the node has
        """
        chosen_node = self.v1.list_node(watch=False, timeout_seconds=15, limit=1, label_selector=node_selector_label)
        return chosen_node.items[0].metadata.labels

    def check_pods_stuck_do_to_insufficient_resource(self, node_selector_label: str = None) -> bool:
        """
            Check if there are any pending pods due to lack of gpu/cpu/memory for them to be placed

            Arguments:
                :param node_selector_label: optional label to use to filter the nodes to get the usage from only a
                subset of nodes that matches that label, defaults to all nodes, should be a string in the format of
                "key=value"

            Returns:
                :return True if there are pods pending due to lack of gpu/cpu/mem, False otherwise
        """

        limited_resources_pending_pod = False
        pod_list = self.v1.list_pod_for_all_namespaces(watch=False, field_selector="status.phase=Pending",
                                                       timeout_seconds=15)
        for pending_pod in pod_list.items:
            if pending_pod.status.conditions[0].reason == "Unschedulable":
                if "nodes" in str(pending_pod.status.conditions[0].message):
                    if ("cpu" in pending_pod.status.conditions[0].message) or \
                            ("memory" in pending_pod.status.conditions[0].message) or \
                            ("gpu" in pending_pod.status.conditions[0].message) or \
                            ("ephemeral-storage" in pending_pod.status.conditions[0].message):
                        if node_selector_label is None:
                            limited_resources_pending_pod = True
                        else:
                            temp_node_selector_label = node_selector_label.split("=")
                            if check_pod_node_affinity(pending_pod) == {
                                temp_node_selector_label[0]: temp_node_selector_label[1]
                            } or check_pod_node_affinity(pending_pod) == {}:
                                limited_resources_pending_pod = True
                        break
        return limited_resources_pending_pod

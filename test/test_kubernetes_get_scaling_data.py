from unittest import TestCase
from spotinst_kubernetes_cluster_autoscaler.kubernetes_get_scaling_data import *
import kubernetes
from pathlib import Path
import os
import httpretty

kube_test_token = os.getenv("TEST_TOKEN", "test")
kube_test_api = os.getenv("TEST_API_ENDPOINT", "https://test:443")


class BaseTests(TestCase):

    def test_KubeGetScaleData__init__in_cluster(self):
        # raising the error because this will only work when running from inside the cluster which is next to impossible
        # to test in any other way so if it raises an error that says "hi i'm configured to work in a cluster but i'm
        # not currently in one" then i'm assuming it got the in_cluster config correctly
        with self.assertRaises(kubernetes.config.config_exception.ConfigException):
            KubeGetScaleData(connection_method="in_cluster")

    def test_KubeGetScaleData__init__kube_config(self):
        kube_config = KubeGetScaleData(connection_method="kube_config", context_name="queen-anne-context",
                                       kubeconfig_path=str(Path(__file__).parent) + "/test_config/test_kube_config")
        self.assertIsInstance(kube_config.v1, kubernetes.client.api.CoreV1Api)
        self.assertIsInstance(kube_config.custom_object_api, kubernetes.client.api.custom_objects_api.CustomObjectsApi)

    def test_KubeGetScaleData__init__api(self):
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        self.assertIsInstance(kube_config.kube_client, kubernetes.client.api_client.ApiClient)
        self.assertIsInstance(kube_config.v1, kubernetes.client.api.CoreV1Api)

    def test_KubeGetScaleData__init__raise_valueerror_on_wrong_connection_method(self):
        with self.assertRaises(ValueError):
            KubeGetScaleData(connection_method="wrong_connection_method")

    def test_KubeGetScaleData_get_number_of_pending_pods(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Pending",
                               body='{"items": ["test1", "test2"]}', status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        self.assertEqual(kube_config.get_number_of_pending_pods(), 2)
        httpretty.disable()
        httpretty.reset()

    def test_KubeGetScaleData_pending_pods_exist_true(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Pending",
                               body='{"items": ["test1", "test2"]}', status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        self.assertTrue(kube_config.pending_pods_exist())
        httpretty.disable()
        httpretty.reset()

    def test_KubeGetScaleData_pending_pods_exist_false(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Pending",
                               body='{"items": []}', status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        self.assertFalse(kube_config.pending_pods_exist())
        httpretty.disable()
        httpretty.reset()

    def test_KubeGetScaleData_get_connected_nodes_count(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/nodes?labelSelector=key2=value2",
                               body='{"items": [{"metadata": {"labels": {"key1": "value1", "key2": "value2"}}}]}',
                               status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        self.assertEqual(kube_config.check_node_group_labels(), {"key1": "value1", "key2": "value2"})
        httpretty.disable()
        httpretty.reset()

    def test_KubeGetScaleData_check_node_group_labels(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/nodes",
                               body='{"items": ["test1", "test2"]}', status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        self.assertEqual(kube_config.get_connected_nodes_count(), 2)
        httpretty.disable()
        httpretty.reset()

    def test_KubeGetScaleData_get_cpu_and_mem_usage_higher_used(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/nodes",
                               body='{"items": [{"status": {"allocatable": {"cpu": "1000m","memory": "5000Mi"}}}]}',
                               status=200)
        httpretty.register_uri(httpretty.GET, kube_test_api + "/apis/metrics.k8s.io/v1beta1/nodes",
                               body='{"items": [{"usage": {"cpu": "500m","memory": "1000Mi"}}]}',
                               status=200)
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Running",
                               body='{"items": [{"name": "test", "spec": {"containers": [{"name": "test", "resources": '
                                    '{"requests": {"cpu": "100m","memory": "100Mi"}}}]}}]}',
                               status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        test_cpu_usage, test_memory_usage = kube_config.get_cpu_and_mem_usage()
        self.assertEqual(test_cpu_usage, 50)
        self.assertEqual(test_memory_usage, 20)
        httpretty.disable()
        httpretty.reset()

    def test_KubeGetScaleData_get_cpu_and_mem_usage_higher_requested(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/nodes",
                               body='{"items": [{"status": {"allocatable": {"cpu": "1000m","memory": "5000Mi"}}}]}',
                               status=200)
        httpretty.register_uri(httpretty.GET, kube_test_api + "/apis/metrics.k8s.io/v1beta1/nodes",
                               body='{"items": [{"usage": {"cpu": "100m","memory": "100Mi"}}]}',
                               status=200)
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Running",
                               body='{"items": [{"name": "test", "spec": {"containers": [{"name": "test", "resources": '
                                    '{"requests": {"cpu": "500m","memory": "1000Mi"}}}]}}]}',
                               status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        test_cpu_usage, test_memory_usage = kube_config.get_cpu_and_mem_usage()
        self.assertEqual(test_cpu_usage, 50)
        self.assertEqual(test_memory_usage, 20)
        httpretty.disable()
        httpretty.reset()

    def test_KubeGetScaleData_get_cpu_and_mem_usage_node_selector_used(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/nodes",
                               body='{"items": [{"metadata": {"name": "ip-1-2-3-4.ec2.internal"},'
                                    '"status": {"allocatable": {"cpu": "1000m","memory": "5000Mi"}}},'
                                    '{"metadata": {"name": "ip-1-2-3-5.ec2.internal"},'
                                    '"status": {"allocatable": {"cpu": "2000m","memory": "10000Mi"}}}]}',
                               status=200)
        httpretty.register_uri(httpretty.GET, kube_test_api + "/apis/metrics.k8s.io/v1beta1/nodes",
                               body='{"items": [{"usage": {"cpu": "100m","memory": "100Mi"}}]}',
                               status=200)
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Running",
                               body='{"items": [{"name": "test", "spec": {"containers": [{"name": "test", "resources": '
                                    '{"requests": {"cpu": "1000m","memory": "2000Mi"}}}]}}]}',
                               status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        test_cpu_usage, test_memory_usage = kube_config.get_cpu_and_mem_usage(node_selector_label="instance_type=test")
        self.assertEqual(test_cpu_usage, 66)
        self.assertEqual(test_memory_usage, 26)
        httpretty.disable()
        httpretty.reset()

    def test_unit_converter_included_units(self):
        reply = unit_converter("10500m")
        self.assertEqual(reply, 10.5)

    def test_unit_converter_custom_added_units(self):
        reply = unit_converter("1Ki")
        self.assertEqual(reply, 1024)

    def test_unit_converter_raise_TypeError_not_included_units(self):
        with self.assertRaises(TypeError):
            unit_converter("10500Ubernonexistingunit")

    def test_check_pods_stuck_do_to_insufficient_resource_no_pods(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Pending",
                               body='{"items": []}', status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        insufficient_resource_pods = kube_config.check_pods_stuck_do_to_insufficient_resource()
        self.assertFalse(insufficient_resource_pods)
        httpretty.disable()
        httpretty.reset()

    def test_check_pods_stuck_do_to_insufficient_resource_single_pending_pods_with_insufficient_cpu(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Pending",
                               body='{"items": [{"status": {"phase": "Pending","conditions": [{"type": "PodScheduled",'
                                    '"status": "False", "lastProbeTime": null, '
                                    '"lastTransitionTime": "2021-05-26T08:47:02Z", '
                                    '"reason": "Unschedulable", '
                                    '"message": "0/13 nodes are available: 13 Insufficient cpu."}]}}]}', status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        insufficient_resource_pods = kube_config.check_pods_stuck_do_to_insufficient_resource()
        self.assertTrue(insufficient_resource_pods)
        httpretty.disable()
        httpretty.reset()

    def test_check_pods_stuck_do_to_insufficient_resource_single_pending_pods_with_insufficient_memory(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Pending",
                               body='{"items": [{"status": {"phase": "Pending","conditions": [{"type": "PodScheduled",'
                                    '"status": "False", "lastProbeTime": null, '
                                    '"lastTransitionTime": "2021-05-26T08:47:02Z", '
                                    '"reason": "Unschedulable", '
                                    '"message": "0/13 nodes are available: 13 Insufficient memory."}]}}]}', status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        insufficient_resource_pods = kube_config.check_pods_stuck_do_to_insufficient_resource()
        self.assertTrue(insufficient_resource_pods)
        httpretty.disable()
        httpretty.reset()

    def test_check_pods_stuck_do_to_insufficient_resource_single_pending_pods_with_insufficient_gpu(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Pending",
                               body='{"items": [{"status": {"phase": "Pending","conditions": [{"type": "PodScheduled",'
                                    '"status": "False", "lastProbeTime": null, '
                                    '"lastTransitionTime": "2021-05-26T08:47:02Z", '
                                    '"reason": "Unschedulable", '
                                    '"message": "0/13 nodes are available: 13 Insufficient gpu."}]}}]}', status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        insufficient_resource_pods = kube_config.check_pods_stuck_do_to_insufficient_resource()
        self.assertTrue(insufficient_resource_pods)
        httpretty.disable()
        httpretty.reset()

    def test_check_pods_stuck_do_to_insufficient_resource_single_pending_pods_with_insufficient_disk(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Pending",
                               body='{"items": [{"status": {"phase": "Pending","conditions": [{"type": "PodScheduled",'
                                    '"status": "False", "lastProbeTime": null, '
                                    '"lastTransitionTime": "2021-05-26T08:47:02Z", '
                                    '"reason": "Unschedulable", '
                                    '"message": "0/13 nodes are available: 13 Insufficient ephemeral-storage."}]}}]}',
                               status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        insufficient_resource_pods = kube_config.check_pods_stuck_do_to_insufficient_resource()
        self.assertTrue(insufficient_resource_pods)
        httpretty.disable()
        httpretty.reset()

    def test_check_pods_stuck_do_to_insufficient_resource_mixed_pending_pods_with_insufficient_resources(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Pending",
                               body='{"items": [{"status": {"phase": "Pending","conditions": [{"type": "PodScheduled",'
                                    '"status": "False", "lastProbeTime": null, '
                                    '"lastTransitionTime": "2021-05-26T08:47:02Z", '
                                    '"reason": "Unschedulable", '
                                    '"message": "crazy reason a pod can not be scheduled with nodes"}]}},'
                                    '{"status": {"phase": "Pending","conditions": [{"type": "PodScheduled",'
                                    '"status": "False", "lastProbeTime": null, '
                                    '"lastTransitionTime": "2021-05-26T08:47:02Z", '
                                    '"reason": "Unschedulable", '
                                    '"message": "0/13 nodes are available: 13 Insufficient cpu."}]}}]}',
                               status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        insufficient_resource_pods = kube_config.check_pods_stuck_do_to_insufficient_resource()
        self.assertTrue(insufficient_resource_pods)
        httpretty.disable()
        httpretty.reset()

    def test_check_pods_stuck_do_to_insufficient_resource_node_group_no_pod_affinity(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Pending?"
                                                              "labelSelector=test_key=test_value",
                               body='{"items": [{"status": {"phase": "Pending","conditions": [{"type": "PodScheduled",'
                                    '"status": "False", "lastProbeTime": null, '
                                    '"lastTransitionTime": "2021-05-26T08:47:02Z", '
                                    '"reason": "Unschedulable", '
                                    '"message": "crazy reason a pod can not be scheduled with nodes"}]}},'
                                    '{"status": {"phase": "Pending","conditions": [{"type": "PodScheduled",'
                                    '"status": "False", "lastProbeTime": null, '
                                    '"lastTransitionTime": "2021-05-26T08:47:02Z", '
                                    '"reason": "Unschedulable", '
                                    '"message": "0/13 nodes are available: 13 Insufficient cpu."}]}}]}',
                               status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        insufficient_resource_pods = kube_config.check_pods_stuck_do_to_insufficient_resource(
            node_selector_label="test_key=test_value")
        self.assertTrue(insufficient_resource_pods)
        httpretty.disable()
        httpretty.reset()

    def test_check_pods_stuck_do_to_insufficient_resource_node_group_node_selector_affinity(self):
        httpretty.enable()
        with open("test/test_responses/eks_node_affinity_response.json", "r") as myfile:
            data = myfile.read().replace('\n', '')
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Pending?"
                                                              "labelSelector=kubernetes.io/e2e-az-name=e2e-az1",
                               body=data, status=200)
        httpretty.register_uri(httpretty.GET, kube_test_api +
                               "/api/v1/nodes?labelSelector=kubernetes.io/e2e-az-name=e2e-az1",
                               body='{"items": [{"metadata": {"labels": {"kubernetes.io/e2e-az-name": '
                                    '"e2e-az1", "key2": "value2"}}}]}',
                               status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        insufficient_resource_pods = kube_config.check_pods_stuck_do_to_insufficient_resource(
            node_selector_label="kubernetes.io/e2e-az-name=e2e-az1")
        self.assertTrue(insufficient_resource_pods)
        httpretty.disable()
        httpretty.reset()

    def test_check_pods_stuck_do_to_insufficient_resource_node_group_node_selector_node_selector(self):
        httpretty.enable()
        with open("test/test_responses/eks_node_selector_response.json", "r") as myfile:
            data = myfile.read().replace('\n', '')
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Pending?"
                                                              "labelSelector=failure-domain.beta.kubernetes.io/zone"
                                                              "=us-east-1b",
                               body=data, status=200)
        httpretty.register_uri(httpretty.GET, kube_test_api +
                               "/api/v1/nodes?labelSelector=failure-domain.beta.kubernetes.io/zone=us-east-1b",
                               body='{"items": [{"metadata": {"labels": {"failure-domain.beta.kubernetes.io/zone": '
                                    '"us-east-1b", "key2": "value2"}}}]}',
                               status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        insufficient_resource_pods = kube_config.check_pods_stuck_do_to_insufficient_resource(
            node_selector_label="failure-domain.beta.kubernetes.io/zone=us-east-1b")
        self.assertTrue(insufficient_resource_pods)
        httpretty.disable()
        httpretty.reset()

    def test_check_pods_stuck_do_to_insufficient_resource_node_group_node_selector_wrong_node_selector(self):
        httpretty.enable()
        with open("test/test_responses/eks_node_selector_response.json", "r") as myfile:
            data = myfile.read().replace('\n', '')
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Pending?"
                                                              "labelSelector=failure-domain.beta.kubernetes.io/zone"
                                                              "=us-east-1b",
                               body=data, status=200)
        httpretty.register_uri(httpretty.GET, kube_test_api +
                               "/api/v1/nodes?labelSelector=failure-domain.beta.kubernetes.io/zone=us-east-1b",
                               body='{"items": [{"metadata": {"labels": {"failure-domain.beta.kubernetes.io/zone": '
                                    '"us-east-1z", "key2": "value2"}}}]}',
                               status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        insufficient_resource_pods = kube_config.check_pods_stuck_do_to_insufficient_resource(
            node_selector_label="failure-domain.beta.kubernetes.io/zone=us-east-1z")
        self.assertFalse(insufficient_resource_pods)
        httpretty.disable()
        httpretty.reset()

    def test_check_pods_stuck_do_to_insufficient_resource_node_group_node_selector_wrong_affinity(self):
        httpretty.enable()
        with open("test/test_responses/eks_node_affinity_response.json", "r") as myfile:
            data = myfile.read().replace('\n', '')
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Pending?"
                                                              "labelSelector=kubernetes.io/e2e-az-name=e2e-az1",
                               body=data, status=200)
        httpretty.register_uri(httpretty.GET, kube_test_api +
                               "/api/v1/nodes?labelSelector=kubernetes.io/e2e-az-name=wrong-az",
                               body='{"items": [{"metadata": {"labels": {"kubernetes.io/e2e-az-name": "wrong-az",'
                                    ' "key2": "value2"}}}]}',
                               status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        insufficient_resource_pods = kube_config.check_pods_stuck_do_to_insufficient_resource(
            node_selector_label="kubernetes.io/e2e-az-name=wrong-az")
        self.assertFalse(insufficient_resource_pods)
        httpretty.disable()
        httpretty.reset()

    def test_check_pods_stuck_do_to_insufficient_resource_pending_pods_due_to_other_reasons(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Pending",
                               body='{"items": [{"status": {"phase": "Pending","conditions": [{"type": "PodScheduled",'
                                    '"status": "False", "lastProbeTime": null, '
                                    '"lastTransitionTime": "2021-05-26T08:47:02Z", '
                                    '"reason": "Unschedulable", '
                                    '"message": "crazy reason a pod can not be scheduled with nodes"}]}}]}', status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        insufficient_resource_pods = kube_config.check_pods_stuck_do_to_insufficient_resource()
        self.assertFalse(insufficient_resource_pods)
        httpretty.disable()
        httpretty.reset()

    def test_check_pod_node_affinity_node_selector(self):
        with open("test/test_responses/eks_node_selector_response.json", "r") as myfile:
            data = myfile.read().replace('\n', '')
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods",
                               body=data, status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        pod_list = kube_config.v1.list_pod_for_all_namespaces(watch=False, timeout_seconds=15)
        response = check_pod_node_affinity(pod_list.items[0])
        self.assertDictEqual(response, {'failure-domain.beta.kubernetes.io/zone': 'us-east-1b'})
        httpretty.disable()
        httpretty.reset()

    def test_check_pod_node_affinity_empty(self):
        with open("test/test_responses/eks_node_selector_empty_response.json", "r") as myfile:
            data = myfile.read().replace('\n', '')
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods",
                               body=data, status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        pod_list = kube_config.v1.list_pod_for_all_namespaces(watch=False, timeout_seconds=15)
        response = check_pod_node_affinity(pod_list.items[0])
        self.assertDictEqual(response, {})
        httpretty.disable()
        httpretty.reset()

    def test_check_pod_node_affinity_node_affinity(self):
        with open("test/test_responses/eks_node_affinity_response.json", "r") as myfile:
            data = myfile.read().replace('\n', '')
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods",
                               body=data, status=200)
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        pod_list = kube_config.v1.list_pod_for_all_namespaces(watch=False, timeout_seconds=15)
        response = check_pod_node_affinity(pod_list.items[0])
        self.assertDictEqual(response, {'kubernetes.io/e2e-az-name': 'e2e-az1'})
        httpretty.disable()
        httpretty.reset()

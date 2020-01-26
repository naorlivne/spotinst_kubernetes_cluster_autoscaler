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
        self.assertIsInstance(kube_config.v1, kubernetes.client.apis.CoreV1Api)
        self.assertIsInstance(kube_config.custom_object_api, kubernetes.client.apis.custom_objects_api.CustomObjectsApi)

    def test_KubeGetScaleData__init__api(self):
        kube_config = KubeGetScaleData(connection_method="api", token=kube_test_token, api_endpoint=kube_test_api)
        self.assertIsInstance(kube_config.kube_client, kubernetes.client.api_client.ApiClient)
        self.assertIsInstance(kube_config.v1, kubernetes.client.apis.CoreV1Api)
        self.assertIsInstance(kube_config.custom_object_api, kubernetes.client.apis.custom_objects_api.CustomObjectsApi)

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

    def test_unit_converter_included_units(self):
        reply = unit_converter("10500m")
        self.assertEqual(reply, 10.5)

    def test_unit_converter_custom_added_units(self):
        reply = unit_converter("1Ki")
        self.assertEqual(reply, 1024)

    def test_unit_converter_raise_TypeError_not_included_units(self):
        with self.assertRaises(TypeError):
            unit_converter("10500Ubernonexistingunit")

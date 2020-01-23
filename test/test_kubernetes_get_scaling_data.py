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

from unittest import TestCase
from spotinst_kubernetes_cluster_autoscaler.kubernetes_get_scaling_data import *
import kubernetes
from pathlib import Path


class BaseTests(TestCase):

    def test_KubeGetScaleData__init__in_cluster(self):
        # raising the error because this will only work when running from inside the cluster which is next to impossible
        # to test
        with self.assertRaises(kubernetes.config.config_exception.ConfigException):
            KubeGetScaleData(connection_method="in_cluster")

    def test_SpotinstScale__init__kube_config(self):
        kube_config = KubeGetScaleData(connection_method="kube_config", context_name="queen-anne-context",
                                       kubeconfig_path=str(Path(__file__).parent) + "/test_config/test_kube_config")
        self.assertIsInstance(kube_config.v1, kubernetes.client.apis.CoreV1Api)
        self.assertIsInstance(kube_config.custom_object_api, kubernetes.client.apis.custom_objects_api.CustomObjectsApi)

    def test_SpotinstScale__init__api(self):
        kube_config = KubeGetScaleData(connection_method="api", token="test", api_endpoint="https://test:443")
        self.assertIsInstance(kube_config.kube_client, kubernetes.client.api_client.ApiClient)
        self.assertIsInstance(kube_config.v1, kubernetes.client.apis.CoreV1Api)
        self.assertIsInstance(kube_config.custom_object_api, kubernetes.client.apis.custom_objects_api.CustomObjectsApi)

    def test_SpotinstScale__init__raise_valueerror_on_wrong_connection_method(self):
        with self.assertRaises(ValueError):
            KubeGetScaleData(connection_method="wrong_connection_method")

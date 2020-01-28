from unittest import TestCase, mock
from spotinst_kubernetes_cluster_autoscaler.configure import *


class BaseTests(TestCase):

    def test_autoscaler_configure_sane_defaults(self):
        with mock.patch('os.environ', {"ELASTIGROUP_ID": "sig-123", "SPOTINST_TOKEN": "test_token"}):
            reply = read_configurations()
            expected_reply = {
                'kube_token': None,
                'kube_api_endpoint': None,
                'kubeconfig_path': os.path.expanduser('~/.kube/config'),
                'kubeconfig_context': None,
                'max_memory_usage': 80,
                'min_memory_usage': 50,
                'max_cpu_usage': 80,
                'min_cpu_usage': 50,
                'seconds_to_check': 10,
                'spotinst_token': "test_token",
                'elastigroup_id': "sig-123",
                'min_node_count': 2,
                'max_node_count': 100
            }
            self.assertTrue(set(expected_reply.items()).issubset(reply.items()))

    def test_autoscaler_raise_error_elastigroup_not_declared(self):
        with self.assertRaises(ValueError):
            read_configurations()

    def test_autoscaler_configure_read_envvar(self):
        with mock.patch('os.environ', {"KUBE_TOKEN": "my_super_secret_token123", "ELASTIGROUP_ID": "sig-123",
                                       "SPOTINST_TOKEN": "test_token"}):
            reply = read_configurations()
            expected_reply = {
                'kube_token': "my_super_secret_token123",
                'kube_api_endpoint': None,
                'kubeconfig_path': os.path.expanduser('~/.kube/config'),
                'kubeconfig_context': None,
                'max_memory_usage': 80,
                'min_memory_usage': 50,
                'max_cpu_usage': 80,
                'min_cpu_usage': 50,
                'seconds_to_check': 10,
                'spotinst_token': "test_token",
                'elastigroup_id': "sig-123",
                'min_node_count': 2,
                'max_node_count': 100
            }
            self.assertTrue(set(expected_reply.items()).issubset(reply.items()))

    def test_terraformize_configure_read_custom_config_folder(self):
        reply = read_configurations(config_folder="test/test_config")
        expected_reply = {
            'kube_token': None,
            'kube_api_endpoint': None,
            'kubeconfig_path': os.path.expanduser('~/.kube/config'),
            'kubeconfig_context': None,
            'max_memory_usage': 80,
            'min_memory_usage': 50,
            'max_cpu_usage': 80,
            'min_cpu_usage': 50,
            'seconds_to_check': 3,
            'spotinst_token': "test_token",
            'elastigroup_id': "sig-123",
            'min_node_count': 2,
            'max_node_count': 100
        }
        self.assertTrue(set(expected_reply.items()).issubset(reply.items()))

    def test_decide_kube_connection_method_api_priority(self):
        reply = decide_kube_connection_method(kube_api_endpoint="mykube.com",
                                              kubeconfig_path="test/test_config/config.yaml")
        self.assertEqual(reply, "api")

    def test_decide_kube_connection_method_kube_config_2nd_priority(self):
        reply = decide_kube_connection_method(kube_api_endpoint=None, kubeconfig_path="test/test_config/config.yaml")
        self.assertEqual(reply, "kube_config")

    def test_decide_kube_connection_method_in_cluster_last_priority_no_kubeconfig_set(self):
        reply = decide_kube_connection_method(kube_api_endpoint=None, kubeconfig_path=None)
        self.assertEqual(reply, "in_cluster")

    def test_decide_kube_connection_method_in_cluster_last_priority(self):
        reply = decide_kube_connection_method(kube_api_endpoint=None, kubeconfig_path="non_existing_config_path")
        self.assertEqual(reply, "in_cluster")

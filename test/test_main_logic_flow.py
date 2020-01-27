from unittest import TestCase, mock
from spotinst_kubernetes_cluster_autoscaler.main_logic_flow import *
import httpretty


kube_test_token = os.getenv("TEST_TOKEN", "test")
kube_test_api = os.getenv("TEST_API_ENDPOINT", "https://test:443")
TEST_TOKEN = "my_auth_token_123"
TEST_ELASTIGROUP = "sig-123"
TEST_CONFIG_DIR = "test/test_config"


class BaseTests(TestCase):

    def test_main_logic_flow_scale_up_stuck_pods(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Pending",
                               body='{"items": ["test1", "test2"]}', status=200)
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
        httpretty.register_uri(httpretty.GET, "https://api.spotinst.io/aws/ec2/group/" + TEST_ELASTIGROUP +
                               "/instanceHealthiness", body='{"response": {"count": 5}}')
        httpretty.register_uri(httpretty.PUT, "https://api.spotinst.io/aws/ec2/group/" + TEST_ELASTIGROUP,
                               body='{"response": {"count": 6}}', status=200)
        with mock.patch('os.environ', {
            "CONFIG_DIR": TEST_CONFIG_DIR,
            "SPOTINST_TOKEN": TEST_TOKEN,
            "KUBE_TOKEN": kube_test_token,
            "KUBE_API_ENDPOINT": kube_test_api
        }):
            action_taken = main_logic_flow()
        self.assertEqual(action_taken, "scaled_up")
        httpretty.disable()
        httpretty.reset()

    def test_main_logic_flow_scale_up_high_cpu(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Pending",
                               body='{"items": []}', status=200)
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/nodes",
                               body='{"items": [{"status": {"allocatable": {"cpu": "1000m","memory": "5000Mi"}}}]}',
                               status=200)
        httpretty.register_uri(httpretty.GET, kube_test_api + "/apis/metrics.k8s.io/v1beta1/nodes",
                               body='{"items": [{"usage": {"cpu": "900m","memory": "1000Mi"}}]}',
                               status=200)
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Running",
                               body='{"items": [{"name": "test", "spec": {"containers": [{"name": "test", "resources": '
                                    '{"requests": {"cpu": "100m","memory": "100Mi"}}}]}}]}',
                               status=200)
        httpretty.register_uri(httpretty.GET, "https://api.spotinst.io/aws/ec2/group/" + TEST_ELASTIGROUP +
                               "/instanceHealthiness", body='{"response": {"count": 5}}')
        httpretty.register_uri(httpretty.PUT, "https://api.spotinst.io/aws/ec2/group/" + TEST_ELASTIGROUP,
                               body='{"response": {"count": 6}}', status=200)
        with mock.patch('os.environ', {
            "CONFIG_DIR": TEST_CONFIG_DIR,
            "SPOTINST_TOKEN": TEST_TOKEN,
            "KUBE_TOKEN": kube_test_token,
            "KUBE_API_ENDPOINT": kube_test_api
        }):
            action_taken = main_logic_flow()
        self.assertEqual(action_taken, "scaled_up")
        httpretty.disable()
        httpretty.reset()

    def test_main_logic_flow_scale_up_high_memory(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Pending",
                               body='{"items": []}', status=200)
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/nodes",
                               body='{"items": [{"status": {"allocatable": {"cpu": "1000m","memory": "5000Mi"}}}]}',
                               status=200)
        httpretty.register_uri(httpretty.GET, kube_test_api + "/apis/metrics.k8s.io/v1beta1/nodes",
                               body='{"items": [{"usage": {"cpu": "100m","memory": "4900Mi"}}]}',
                               status=200)
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Running",
                               body='{"items": [{"name": "test", "spec": {"containers": [{"name": "test", "resources": '
                                    '{"requests": {"cpu": "100m","memory": "100Mi"}}}]}}]}',
                               status=200)
        httpretty.register_uri(httpretty.GET, "https://api.spotinst.io/aws/ec2/group/" + TEST_ELASTIGROUP +
                               "/instanceHealthiness", body='{"response": {"count": 5}}')
        httpretty.register_uri(httpretty.PUT, "https://api.spotinst.io/aws/ec2/group/" + TEST_ELASTIGROUP,
                               body='{"response": {"count": 6}}', status=200)
        with mock.patch('os.environ', {
            "CONFIG_DIR": TEST_CONFIG_DIR,
            "SPOTINST_TOKEN": TEST_TOKEN,
            "KUBE_TOKEN": kube_test_token,
            "KUBE_API_ENDPOINT": kube_test_api
        }):
            action_taken = main_logic_flow()
        self.assertEqual(action_taken, "scaled_up")
        httpretty.disable()
        httpretty.reset()

    def test_main_logic_flow_scale_down_low_usage(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Pending",
                               body='{"items": []}', status=200)
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/nodes",
                               body='{"items": [{"status": {"allocatable": {"cpu": "1000m","memory": "5000Mi"}}}]}',
                               status=200)
        httpretty.register_uri(httpretty.GET, kube_test_api + "/apis/metrics.k8s.io/v1beta1/nodes",
                               body='{"items": [{"usage": {"cpu": "100m","memory": "400Mi"}}]}',
                               status=200)
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Running",
                               body='{"items": [{"name": "test", "spec": {"containers": [{"name": "test", "resources": '
                                    '{"requests": {"cpu": "100m","memory": "100Mi"}}}]}}]}',
                               status=200)
        httpretty.register_uri(httpretty.GET, "https://api.spotinst.io/aws/ec2/group/" + TEST_ELASTIGROUP +
                               "/instanceHealthiness", body='{"response": {"count": 5}}')
        httpretty.register_uri(httpretty.PUT, "https://api.spotinst.io/aws/ec2/group/" + TEST_ELASTIGROUP,
                               body='{"response": {"count": 6}}', status=200)
        with mock.patch('os.environ', {
            "CONFIG_DIR": TEST_CONFIG_DIR,
            "SPOTINST_TOKEN": TEST_TOKEN,
            "KUBE_TOKEN": kube_test_token,
            "KUBE_API_ENDPOINT": kube_test_api
        }):
            action_taken = main_logic_flow()
        self.assertEqual(action_taken, "scaled_down")
        httpretty.disable()
        httpretty.reset()

    def test_main_logic_flow_no_rescaling_needed(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Pending",
                               body='{"items": []}', status=200)
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/nodes",
                               body='{"items": [{"status": {"allocatable": {"cpu": "1000m","memory": "5000Mi"}}}]}',
                               status=200)
        httpretty.register_uri(httpretty.GET, kube_test_api + "/apis/metrics.k8s.io/v1beta1/nodes",
                               body='{"items": [{"usage": {"cpu": "500m","memory": "2500Mi"}}]}',
                               status=200)
        httpretty.register_uri(httpretty.GET, kube_test_api + "/api/v1/pods?fieldSelector=status.phase=Running",
                               body='{"items": [{"name": "test", "spec": {"containers": [{"name": "test", "resources": '
                                    '{"requests": {"cpu": "100m","memory": "100Mi"}}}]}}]}',
                               status=200)
        httpretty.register_uri(httpretty.GET, "https://api.spotinst.io/aws/ec2/group/" + TEST_ELASTIGROUP +
                               "/instanceHealthiness", body='{"response": {"count": 5}}')
        httpretty.register_uri(httpretty.PUT, "https://api.spotinst.io/aws/ec2/group/" + TEST_ELASTIGROUP,
                               body='{"response": {"count": 6}}', status=200)
        with mock.patch('os.environ', {
            "CONFIG_DIR": TEST_CONFIG_DIR,
            "SPOTINST_TOKEN": TEST_TOKEN,
            "KUBE_TOKEN": kube_test_token,
            "KUBE_API_ENDPOINT": kube_test_api
        }):
            action_taken = main_logic_flow()
        self.assertIsNone(action_taken)
        httpretty.disable()
        httpretty.reset()

    def test_main_logic_raise_exception(self):
        with self.assertRaises(SystemExit):
            main_logic_flow()

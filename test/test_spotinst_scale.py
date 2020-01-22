from unittest import TestCase
from spotinst_kubernetes_cluster_autoscaler.spotinst_scale import *
import httpretty

TEST_TOKEN = "my_auth_token_123"
TEST_ELASTIGROUP = "sig-1234567"


class BaseTests(TestCase):

    def test_SpotinstScale__init__(self):
        expected_headers = {
            'authorization': 'Bearer ' + TEST_TOKEN,
            'cache-control': 'no-cache',
            'content-type': 'application/json'
        }
        spotinst_connection = SpotinstScale(auth_token=TEST_TOKEN, elastigroup=TEST_ELASTIGROUP)
        self.assertEqual(spotinst_connection.elastigroup, TEST_ELASTIGROUP)
        self.assertEqual(spotinst_connection.url, "https://api.spotinst.io/aws/ec2/group/" + TEST_ELASTIGROUP +
                         "/instanceHealthiness")
        self.assertEqual(spotinst_connection.headers, expected_headers)

    def test_SpotinstScale_get_spotinst_instances(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, "https://api.spotinst.io/aws/ec2/group/" + TEST_ELASTIGROUP +
                               "/instanceHealthiness", body='{"response": {"count": 5}}')
        spotinst_connection = SpotinstScale(auth_token=TEST_TOKEN, elastigroup=TEST_ELASTIGROUP)
        response = spotinst_connection.get_spotinst_instances()
        httpretty.disable()
        httpretty.reset()
        self.assertEqual(response, 5)

    def test_SpotinstScale_set_spotinst_elastigroup_size(self):
        httpretty.enable()
        for status_code in range(200, 208):
            httpretty.register_uri(httpretty.PUT, "https://api.spotinst.io/aws/ec2/group/" + TEST_ELASTIGROUP,
                                   body='{"response": {"count": 6}}', status=status_code)
            spotinst_connection = SpotinstScale(auth_token=TEST_TOKEN, elastigroup=TEST_ELASTIGROUP)
            response = spotinst_connection.set_spotinst_elastigroup_size(6)
            self.assertTrue(response)
        httpretty.disable()
        httpretty.reset()

    def test_SpotinstScale_set_spotinst_elastigroup_size_raise_error_on_failure(self):
        httpretty.enable()
        for status_code in [100, 300]:
            httpretty.register_uri(httpretty.PUT, "https://api.spotinst.io/aws/ec2/group/" + TEST_ELASTIGROUP,
                                   body='{"response": {"count": 6}}', status=status_code)
            spotinst_connection = SpotinstScale(auth_token=TEST_TOKEN, elastigroup=TEST_ELASTIGROUP)
            with self.assertRaises(Exception):
                spotinst_connection.set_spotinst_elastigroup_size(6)
        httpretty.disable()
        httpretty.reset()

    def test_SpotinstScale_get_spotinst_scale_up(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, "https://api.spotinst.io/aws/ec2/group/" + TEST_ELASTIGROUP +
                               "/instanceHealthiness", body='{"response": {"count": 5}}')
        httpretty.register_uri(httpretty.PUT, "https://api.spotinst.io/aws/ec2/group/" + TEST_ELASTIGROUP,
                               body='{"response": {"count": 6}}', status=200)
        spotinst_connection = SpotinstScale(auth_token=TEST_TOKEN, elastigroup=TEST_ELASTIGROUP)
        response = spotinst_connection.scale_up()
        self.assertEqual(response, 6)
        httpretty.disable()
        httpretty.reset()

    def test_SpotinstScale_get_spotinst_scale_down(self):
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, "https://api.spotinst.io/aws/ec2/group/" + TEST_ELASTIGROUP +
                               "/instanceHealthiness", body='{"response": {"count": 5}}')
        httpretty.register_uri(httpretty.PUT, "https://api.spotinst.io/aws/ec2/group/" + TEST_ELASTIGROUP,
                               body='{"response": {"count": 6}}', status=200)
        spotinst_connection = SpotinstScale(auth_token=TEST_TOKEN, elastigroup=TEST_ELASTIGROUP)
        response = spotinst_connection.scale_down()
        self.assertEqual(response, 4)
        httpretty.disable()
        httpretty.reset()

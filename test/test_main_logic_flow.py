from unittest import TestCase, mock
from spotinst_kubernetes_cluster_autoscaler.main_logic_flow import *


class BaseTests(TestCase):

    def test_main_logic_flow_scale_up_stuck_pods(self):
        pass

    def test_main_logic_flow_scale_up_high_cpu(self):
        pass

    def test_main_logic_flow_scale_up_high_memory(self):
        pass

    def test_main_logic_flow_scale_down_low_usage(self):
        pass

    def test_main_logic_flow_no_rescaling_needed(self):
        pass

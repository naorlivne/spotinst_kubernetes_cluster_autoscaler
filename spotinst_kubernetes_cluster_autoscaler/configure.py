import os
from parse_it import ParseIt
from typing import Optional


def decide_kube_connection_method(kube_api_endpoint: Optional[str] = None,
                                  kubeconfig_path: Optional[str] = None,) -> str:
    """
    Will decide on the proper way to connect to the kubernetes API (via API request, as declered on kubeconfig file or
    via using in cluster configuration based on what the user pass, priority is api>kubeconfig>in_cluster

    Arguments:
        :param kube_api_endpoint: the kubernetes api endpoint
        :param kubeconfig_path: the path to the kubeconfig file

    Returns:
        :return kube_connection_method: one of: "api", "kube_config" or "in_cluster"
    """
    if kube_api_endpoint is not None:
        kube_connection_method = "api"
    elif kubeconfig_path is not None and \
            os.path.isfile(kubeconfig_path) is True:
        kube_connection_method = "kube_config"
    else:
        kube_connection_method = "in_cluster"
    return kube_connection_method


def read_configurations(config_folder: str = "config") -> dict:
    """
    Will create a config dict that includes all of the configurations for the autoscaler by aggregating from all valid
    config sources (files, envvars, cli args, etc) & using sane defaults on config params that are not declared

    Arguments:
        :param config_folder: the folder which all configuration file will be read from recursively

    Returns:
        :return config: a dict of all configurations needed for autoscaler to work
    """
    print("reading config variables")

    config = {}
    parser = ParseIt(config_location=config_folder, recurse=True)

    config["kube_token"] = parser.read_configuration_variable("kube_token", default_value=None)
    config["kube_api_endpoint"] = parser.read_configuration_variable("kube_api_endpoint", default_value=None)
    kubeconfig_file = os.path.expanduser("~/.kube/config")
    config["kubeconfig_path"] = parser.read_configuration_variable("kubeconfig_path", default_value=kubeconfig_file)
    config["kubeconfig_context"] = parser.read_configuration_variable("kubeconfig_context", default_value=None)
    config["max_memory_usage"] = parser.read_configuration_variable("max_memory_usage", default_value=80)
    config["min_memory_usage"] = parser.read_configuration_variable("min_memory_usage", default_value=50)
    config["max_cpu_usage"] = parser.read_configuration_variable("max_cpu_usage", default_value=80)
    config["min_cpu_usage"] = parser.read_configuration_variable("min_cpu_usage", default_value=50)
    config["seconds_to_check"] = parser.read_configuration_variable("seconds_to_check", default_value=30)
    config["spotinst_token"] = parser.read_configuration_variable("spotinst_token", required=True)
    config["kube_connection_method"] = decide_kube_connection_method(kube_api_endpoint=config["kube_api_endpoint"],
                                                                     kubeconfig_path=config["kubeconfig_path"])
    config["elastigroup_id"] = parser.read_configuration_variable("elastigroup_id", required=True)
    config["min_node_count"] = parser.read_configuration_variable("min_node_count", default_value=2)
    config["max_node_count"] = parser.read_configuration_variable("max_node_count", default_value=100)
    config["spotinst_account"] = parser.read_configuration_variable("spotinst_account", required=True)
    config["scale_up_count"] = parser.read_configuration_variable("scale_up_count", default_value=1)
    config["scale_down_count"] = parser.read_configuration_variable("scale_down_count", default_value=1)
    config["scale_up_active"] = parser.read_configuration_variable("scale_up_active", default_value=True)
    config["scale_down_active"] = parser.read_configuration_variable("scale_down_active", default_value=True)
    config["scale_on_pending_pods"] = parser.read_configuration_variable("scale_on_pending_pods", default_value=True)
    config["node_selector_label"] = parser.read_configuration_variable("node_selector_label", default_value=None)

    return config

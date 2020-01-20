import os
from parse_it import ParseIt


def decide_kube_connection_method(connection_config: dict) -> str:
    """
    Will decide on the proper way to connect to the kubernetes API (via API request, as declered on kubeconfig file or
    via using in cluster configuration based on what the user pass, priority is api>kubeconfig>in_cluster

    Arguments:
        :param connection_config: the configuration dict which all configuration of possible kubernetes connections are
        located in

    Returns:
        :return kube_connection_method: one of: "api", "kube_config" or "in_cluster"
    """
    if connection_config["kube_api_endpoint"] is not None:
        kube_connection_method = "api"
    elif connection_config["kubeconfig_path"] is not None and \
            os.path.isfile(connection_config["kubeconfig_path"]) is True:
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
    config["seconds_to_check"] = parser.read_configuration_variable("seconds_to_check", default_value=10)
    config["spotinst_account"] = parser.read_configuration_variable("spotinst_account", default_value=None)
    config["spotinst_token"] = parser.read_configuration_variable("spotinst_token", default_value=None)
    config["kube_connection_method"] = decide_kube_connection_method(config)

    return config

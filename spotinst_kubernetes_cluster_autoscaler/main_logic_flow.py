from spotinst_kubernetes_cluster_autoscaler.configure import *
from spotinst_kubernetes_cluster_autoscaler.kubernetes_get_scaling_data import *
from spotinst_kubernetes_cluster_autoscaler.spotinst_scale import *


def main_logic_flow():
    """
        The main logic process, first read the configuration options, then get the current cluster CPU, Memory usage &
        check if there are any pod deployments waiting for resources, then pass those params to the logic which decides
        if it needs to scale up or down and then scale the spotinst elastigroup if needed before exiting
    """
    try:
        # read configuration
        print("Starting spotinst_kubernetes_cluster_autoscaler")
        configuration = read_configurations(os.getenv("CONFIG_DIR", "config"))

        # create kube connection object
        kube_connection = KubeGetScaleData(connection_method=configuration["kube_connection_method"],
                                           api_endpoint=configuration["kube_api_endpoint"],
                                           context_name=configuration["kubeconfig_context"],
                                           token=configuration["kube_token"],
                                           kubeconfig_path=configuration["kubeconfig_path"])

        # create spotinst connection object
        spotinst_connection = SpotinstScale(auth_token=configuration["spotinst_token"],
                                            elastigroup=configuration["elastigroup_id"],
                                            spotinst_account=configuration["spotinst_account"],
                                            min_nodes=configuration["min_node_count"],
                                            max_nodes=configuration["max_node_count"])

        # check if there are any stuck pods and if there are scale the cluster up
        print("checking if there are any stuck pods")
        if kube_connection.pending_pods_exist(seconds_to_wait_between_checks=configuration["seconds_to_check"]) is True:
            pending_pods_number = kube_connection.get_number_of_pending_pods()
            print("there are " + str(pending_pods_number) + " pending pods, scaling up number of kubernetes nodes")
            server_count = spotinst_connection.scale_up(configuration["scale_up_count"])
            print("scaled up to " + str(server_count) + "servers")
            action_taken = "scaled_up"
        # otherwise check the cpu & memory usage
        else:
            used_cpu_percentage, used_memory_percentage = kube_connection.get_cpu_and_mem_usage()
            print("current cluster CPU usage is " + str(used_cpu_percentage) + "%")
            print("current cluster memory usage is " + str(used_memory_percentage) + "%")
            # on high cpu/memory usage scale up, it's enough to have just one of them be high to scale up
            if used_cpu_percentage >= configuration["max_cpu_usage"] or \
                    used_memory_percentage >= configuration["max_memory_usage"]:
                print("scaling up due to high memory/cpu usage")
                server_count = spotinst_connection.scale_up(configuration["scale_up_count"])
                print("scaled up to " + str(server_count) + "servers")
                action_taken = "scaled_up"
            # on low cpu/memory usage scale down, both are needed to be low to scale down
            elif used_cpu_percentage < configuration["min_cpu_usage"] and \
                    used_memory_percentage < configuration["min_memory_usage"]:
                print("scaling down due to low memory/cpu usage")
                server_count = spotinst_connection.scale_down(configuration["scale_down_count"])
                print("scaled down to " + str(server_count) + "servers")
                action_taken = "scaled_down"
            # otherwise were done here
            else:
                print("no rescaling needed, exiting")
                action_taken = None

        return action_taken

    except Exception as e:
        print("failed main logic flow - exiting")
        print(e, file=sys.stderr)
        exit(2)

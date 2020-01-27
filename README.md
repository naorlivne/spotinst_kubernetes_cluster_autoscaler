# spotinst_kubernetes_cluster_autoscaler

a kubernetes autoscaler to scale kubernetes nodes running as a spotinst elastigroup based on CPU/mem/disk usage and unplacable pods

Drone.io CI/CD unit tests & auto push status: [![Build Status](https://cloud.drone.io/api/badges/naorlivne/spotinst_kubernetes_cluster_autoscaler/status.svg)](https://cloud.drone.io/naorlivne/spotinst_kubernetes_cluster_autoscaler)

Code coverage: [![codecov](https://codecov.io/gh/naorlivne/spotinst_kubernetes_cluster_autoscaler/branch/master/graph/badge.svg)](https://codecov.io/gh/naorlivne/spotinst_kubernetes_cluster_autoscaler)

## configuring

Configuring is done using [parse_it](https://github.com/naorlivne/parse_it) which means that you can configure the autoscaler by placing configuration files (of your chosen format) in the configuration folder (`config` by default, can be changed with the `CONFIG_DIR` envvar ) or by setting the UPPERCASE version of the variables below:

| value              | envvar             | default value  | notes                                                                                                               |
|--------------------|--------------------|----------------|---------------------------------------------------------------------------------------------------------------------|
| kube_token         | KUBE_TOKEN         | None           | Kubernetes token used to connect to the cluster, not needed if running in cluster or using kubeconfig file          |
| kube_api_endpoint  | KUBE_API_ENDPOINT  | None           | Kubernetes API endpoint used to connect to the cluster, not needed if running in cluster or using kubeconfig file   |
| kubeconfig_path    | KUBECONFIG_PATH    | ~/.kube/config | Path to kubeconfig file used to connect to the cluster, not needed if running in cluster or using token auth        |
| kubeconfig_context | KUBECONFIG_CONTEXT | None           | Context of the kubeconfig file used to connect to the cluster, not needed if running in cluster or using token auth |
| max_memory_usage   | MAX_MEMORY_USAGE   | 80             | Maximum memory usage above which the cluster will be autoscaled, in percent (1 to 100)                              |
| min_memory_usage   | MIN_MEMORY_USAGE   | 50             | Minimum memory usage above which the cluster will be autoscaled, in percent (1 to 100)                              |
| max_cpu_usage      | MAX_CPU_USAGE      | 80             | Maximum CPU usage above which the cluster will be autoscaled, in percent (1 to 100)                                 |
| min_cpu_usage      | MIN_CPU_USAGE      | 50             | Minimum CPU usage above which the cluster will be autoscaled, in percent (1 to 100)                                 |
| seconds_to_check   | SECONDS_TO_CHECK   | 10             | time to wait before double checking of pending containers before scaling up if they are still in a pending state    |
| spotinst_token     | SPOTINST_TOKEN     |                | Required, token used to connect to spotinst                                                                         |
| elastigroup_id     | ELASTIGROUP_ID     |                | Required, the elastigroup ID of your kubernetes nodes in spotinst                                                   |
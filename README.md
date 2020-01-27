# spotinst_kubernetes_cluster_autoscaler

a kubernetes autoscaler to scale kubernetes nodes running as a spotinst elastigroup based on CPU/mem/disk usage and unplacable pods

Drone.io CI/CD unit tests & auto push status: [![Build Status](https://cloud.drone.io/api/badges/naorlivne/spotinst_kubernetes_cluster_autoscaler/status.svg)](https://cloud.drone.io/naorlivne/spotinst_kubernetes_cluster_autoscaler)

Code coverage: [![codecov](https://codecov.io/gh/naorlivne/spotinst_kubernetes_cluster_autoscaler/branch/master/graph/badge.svg)](https://codecov.io/gh/naorlivne/spotinst_kubernetes_cluster_autoscaler)

## configuring

Configuring is done using [parse_it](https://github.com/naorlivne/parse_it) which means that you can configure the autoscaler by placing configuration files (of your chosen format) in the configuration folder (`config` by default, can be changed with the `CONFIG_DIR` envvar ) or by setting the UPPERCASE version of the variables below:

* kube_token
* kube_api_endpoint
* kubeconfig_path
*
*
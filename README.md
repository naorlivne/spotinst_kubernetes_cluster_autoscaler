# Spotinst_kubernetes_cluster_autoscaler

A kubernetes autoscaler to scale kubernetes nodes running as a spotinst elastigroup based on CPU/mem/disk usage and unplacable pods

Drone.io CI/CD unit tests & auto push status: [![Build Status](https://cloud.drone.io/api/badges/naorlivne/spotinst_kubernetes_cluster_autoscaler/status.svg)](https://cloud.drone.io/naorlivne/spotinst_kubernetes_cluster_autoscaler)

Code coverage: [![codecov](https://codecov.io/gh/naorlivne/spotinst_kubernetes_cluster_autoscaler/branch/master/graph/badge.svg)](https://codecov.io/gh/naorlivne/spotinst_kubernetes_cluster_autoscaler)

# Dependencies

The autoscaler requires the following:

* A kubernetes cluster 
* A spotinst group which runs the kubernetes cluster nodes
* [metrics-server](https://github.com/kubernetes-sigs/metrics-server) installed & configured on the kubernetes cluster

## Configuration parameters

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

## Running outside the cluster

You need to be able to connect to both the spotinst API (which is done with the `spotinst_token` & `elastigroup_id` variables) & to your Kubernetes cluster API, the following can be done in one of 2 ways outside the cluster:

* Using a kubeconfig file, this will require mounting the kubeconfig inside the autoscaler container and setting the `kubeconfig_path` & `kubeconfig_context` variables
* Using a Bearer token with the `kube_api_endpoint` & `kube_token`

When running the autoscaler outside the cluster the simplest way is to run everything via envars, for example:

```shell script
sudo docker run -e kube_token=my_kube_token -e kube_api_endpoint=my-kube.my-domain.com -e spotinst_token=my_spoinst_token -e elastigroup_id=sig-123XXXX naorlivne/spotinst_kubernetes_cluster_autoscaler
```

Note that the autoscaler is designed to run as a cronjob so it will exit once finished! if you plan on running it outside the cluster in a prod env it is recommended to wrap it as a cron task

## Running inside the cluster

Inside the cluster running the autoscaler as a cron_job is the recommended way to go, if your cluster is configured with RBAC you will also need to grant it a service user that is allowed to read the state of the cluster.

### with RBAC configured

When RBAC is enabled you need to configure read-only access to the kubernetes cluster & to the [metrics-server](https://github.com/kubernetes-sigs/metrics-server).

[This configuration](kubernetes_in_cluster_example_config/with_rbac.yaml) provides an example on how to run spotinst_kubernetes_cluster_autoscaler on a kubernetes cluster that's configured with RBAC as cron job every minute.

You can run it with the following command:

```shell script
kubectl apply -f https://raw.githubusercontent.com/naorlivne/spotinst_kubernetes_cluster_autoscaler/master/kubernetes_in_cluster_example_config/with_rbac.yaml
```

Be aware that at minimum you will need to change the values of `SPOTINST_TOKEN` & `ELASTIGROUP_ID` envvars to your own spotinst token & elastigroup ID

### without RBAC configured

[This configuration](kubernetes_in_cluster_example_config/without_rbac.yaml) provides an example on how to run spotinst_kubernetes_cluster_autoscaler on a kubernetes cluster that's configured without RBAC as cron job every minute.

You can run it with the following command:

```shell script
kubectl apply -f https://raw.githubusercontent.com/naorlivne/spotinst_kubernetes_cluster_autoscaler/master/kubernetes_in_cluster_example_config/without_rbac.yaml
```

Be aware that at minimum you will need to change the values of `SPOTINST_TOKEN` & `ELASTIGROUP_ID` envvars to your own spotinst token & elastigroup ID

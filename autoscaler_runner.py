from spotinst_kubernetes_cluster_autoscaler.main_logic_flow import *


# this will first run the initial setup a single time then will loop over the main logic loop flow forever
if __name__ == "__main__":
    try:
        main_logic_flow()
    except Exception as e:
        print(e, file=sys.stderr)
        exit(2)

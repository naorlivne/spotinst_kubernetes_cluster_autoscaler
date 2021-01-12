import requests
import sys


class SpotinstScale:
    """
       This class does everything related to spotinst, this includes figuring out the current number of nodes in the
       cluster & sending scale up/down requests to said group
    """

    def __init__(self, auth_token: str, elastigroup: str, spotinst_account: str, min_nodes: int, max_nodes: int):
        """
           Init the class with the basic data needed to use the spotinst API that is always common between the different
           calls needed

           Arguments:
               :param auth_token: the spotinst api token
               :param elastigroup: the elastigroup ID which the nodes are part of
               :param spotinst_account: the spotinst account ID which the elastigroup is located at
               :param min_nodes: the minimum number of nodes wanted in the cluster elastigroup
               :param max_nodes: the maximum number of nodes wanted in the cluster elastigroup
        """
        self.elastigroup = elastigroup
        self.headers = {
            'authorization': "Bearer " + auth_token,
            'content-type': "application/json",
            'cache-control': "no-cache"
        }
        self.min_nodes = min_nodes
        self.max_nodes = max_nodes
        self.spotinst_account = spotinst_account
        self.url = "https://api.spotinst.io/aws/ec2/group/" + self.elastigroup + "/instanceHealthiness?accountId=" + \
                   self.spotinst_account

    def get_spotinst_instances(self) -> int:
        """
            Get the current number of spotinst nodes

            Returns:
                :return current number of nodes in the elastigroup
        """
        url = "https://api.spotinst.io/aws/ec2/group/" + self.elastigroup + "/instanceHealthiness" + "?accountId=" + \
              self.spotinst_account

        headers = self.headers

        spotinst_response = requests.request("GET", url, headers=headers)
        response_json = spotinst_response.json()

        return int(response_json["response"]["count"])

    def set_spotinst_elastigroup_size(self, wanted_nodes_number: int) -> int:
        """
            Set the spotinst elastigroup size

            Arguments:
                :param wanted_nodes_number: the number of nodes wanted in the cluster elastigroup

            Returns:
                :return True: if the scaling worked as desired

            Raises:
                :raise Exception: if the spotinst API failed to scale up/down as desired
        """
        url = "https://api.spotinst.io/aws/ec2/group/" + self.elastigroup + "?accountId=" + self.spotinst_account

        payload = "{\"group\": { \"capacity\": { \"target\": " + str(wanted_nodes_number) + ", \"minimum\": " \
                  + str(self.min_nodes) + ", \"maximum\":" + str(self.max_nodes) + "}}}"
        headers = self.headers

        response = requests.request("PUT", url, data=payload, headers=headers)
        if 200 <= response.status_code < 300:
            return True
        else:
            print(response, file=sys.stderr)
            print("spotinst API didn't accept the size increase", file=sys.stderr)
            raise Exception

    def scale_up(self, scale_count: int = 1) -> int:
        """
            Scale up the current number of nodes by scale_count

            Arguments:
                :param scale_count: the number of nodes you want to add to the cluster

            Returns:
                :return wanted_number_of_nodes: the new number of nodes in the elastigroup
        """
        wanted_number_of_nodes = self.get_spotinst_instances() + scale_count
        if self.set_spotinst_elastigroup_size(wanted_number_of_nodes) is True:
            return wanted_number_of_nodes

    def scale_down(self, scale_count: int = 1) -> int:
        """
            Scale down the current number of nodes by scale_count

            Arguments:
                :param scale_count: the number of nodes you want to add to the cluster

            Returns:
                :return wanted_number_of_nodes: the new number of nodes in the elastigroup
        """
        wanted_number_of_nodes = self.get_spotinst_instances() - scale_count
        if self.set_spotinst_elastigroup_size(wanted_number_of_nodes) is True:
            return wanted_number_of_nodes

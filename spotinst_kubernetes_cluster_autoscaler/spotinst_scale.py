import requests
import sys


class SpotinstScale:
    """
       This class does everything related to spotinst, this includes figuring out the current number of nodes in the
       cluster & sending scale up/down requests to said group
    """

    def __init__(self, auth_token: str, elastigroup: str):
        """
           Init the class with the basic data needed to use the spotinst API that is always common between the different
           calls needed

           Arguments:
               :param auth_token: the spotinst api token
               :param elastigroup: the elastigroup ID which the nodes are part of
        """
        self.elastigroup = elastigroup
        self.url = "https://api.spotinst.io/aws/ec2/group/" + self.elastigroup + "/instanceHealthiness"
        self.headers = {
            'authorization': "Bearer " + auth_token,
            'content-type': "application/json",
            'cache-control': "no-cache"
        }

    def get_spotinst_instances(self) -> int:
        """
            Get the current number of spotinst nodes

            Returns:
                :return current number of nodes in the elastigroup
        """
        url = "https://api.spotinst.io/aws/ec2/group/" + self.elastigroup + "/instanceHealthiness"

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
        url = "https://api.spotinst.io/aws/ec2/group/" + self.elastigroup

        payload = "{\"group\": { \"capacity\": { \"target\": " + str(wanted_nodes_number) + ", \"minimum\": " \
                  + str(wanted_nodes_number) + ", \"maximum\":" + str(wanted_nodes_number) + "}}}"
        headers = self.headers

        response = requests.request("PUT", url, data=payload, headers=headers)
        if 200 <= response.status_code < 300:
            return True
        else:
            print(response, file=sys.stderr)
            print("spotinst API didn't accept the size increase", file=sys.stderr)
            raise Exception

    def scale_up(self):
        """
            Scale up the current number of nodes by 1

            Returns:
                :return wanted_number_of_nodes: the new number of nodes in the elastigroup
        """
        wanted_number_of_nodes = self.get_spotinst_instances() + 1
        if self.set_spotinst_elastigroup_size(wanted_number_of_nodes) is True:
            return wanted_number_of_nodes

    def scale_down(self):
        """
            Scale down the current number of nodes by 1

            Returns:
                :return wanted_number_of_nodes: the new number of nodes in the elastigroup
        """
        wanted_number_of_nodes = self.get_spotinst_instances() - 1
        if self.set_spotinst_elastigroup_size(wanted_number_of_nodes) is True:
            return wanted_number_of_nodes

import json
import requests
from datetime import datetime, timedelta

class CentraAPI(object):

    def __init__(self, management_url=""):
        """
        Initializes an API object that is used
        to make consistent calls to the Guardicore Centra API
        """

        self.management_url = management_url
        self.session = requests.Session()

        self.session.headers.update({
            'Content-Type': 'application/json'
        })

    def authenticate(self, username, password):
        """
        Authenticates to the Guardicore Centra API and 
        gets back an access_token
        """

        auth_body = {
            "username": username,
            "password": password
        }

        response = self.session.post(f"https://{self.management_url}/api/v3.0/authenticate", data=json.dumps(auth_body))
        if response.status_code == 200:
            data = response.json()

            # If the account in use has MFA enabled, raise a ValueError
            if '2fa_temp_token' in data:
                raise ValueError("Guardicore credentials required MFA.  Use an acccount without MFA.")

            self.session.headers.update({
                "Authorization": f"Bearer {data['access_token']}"
            })

        if response.status_code == 401:
            raise ValueErro("Incorrect Guardicore username or password.")
    
    def block_ip(self, ip, rule_set, direction):
        """
        Adds an IP address to a policy rule to block
        traffic to and/or from the IP in question
        """

        if direction not in ["DESTINATION","SOURCE","BOTH"]:
            raise ValueError("direction must either be DESTINATION, SOURCE or BOTH")

        if direction in ["DESTINATION", "BOTH"]:
            data = {
                "direction": "DESTINATION",
                "reputation_type": "top_ips",
                "ruleset_name": rule_set + " | Outbound",
                "value": ip
            }
            self.session.post(f"https://{self.management_url}/api/v3.0/widgets/malicious-reputation-block", data=json.dumps(data))
            
        if direction in ["SOURCE", "BOTH"]:
            data = {
                "direction": "SOURCE",
                "reputation_type": "top_ips",
                "ruleset_name": rule_set + " | Inbound",
                "value": ip
            }
            self.session.post(f"https://{self.management_url}/api/v3.0/widgets/malicious-reputation-block", data=json.dumps(data))


    def get_incidents(self, tags=[], tag__not=["Acknowledged"], limit=500, from_hours=24):
        """
        Fetches a list of incidents from Centra UI based on
        a set of criteria
        """

        tag_list = ",".join(tags)
        tag__not = ",".join(tag__not)
        from_time = int((datetime.now() - timedelta(hours=from_hours)).timestamp()) * 1000
        to_time = int(datetime.now().timestamp()) * 1000

        url = f"https://{self.management_url}/api/v3.0/incidents?tag={tag_list}&tag__not={tag__not}&from_time={from_time}&to_time={to_time}&limit={limit}"
        response = self.session.get(url)
        if response.status_code == 200:
            data = response.json()
            return data['objects']
        else:
            return []

    def tag_incident(self, id, tags):
        """
        Tags an incident with user and system defined
        tags so analysts can triage a threat more 
        readily or look back as to why a threat was triaged
        the way it was 
        """

        # Assign all the tags
        for tag in tags:
            data = {
                "action": "add",
                "tag_name": tag,
                "negate_args": None,
                "ids": [id]
            }
            self.session.post(f"https://{self.management_url}/api/v3.0/incidents/tag", data=json.dumps(data))

    def acknowledge_incident(self, ids=[]):
        """
        Sets the Acknowledged tag on any incidents
        present in the ids variable
        """

        # Make sure this is a list
        if not isinstance(ids, list):
            raise TypeError("ids should be a list")

        data = {
            "ids": ids,
            "negate_args": None
        }
        self.session.post(f"https://{self.management_url}/api/v3.0/incidents/acknowledge", data=json.dumps(data))

    def get_inner(self, destination, source):
        """
        Returns the IP that is part of an incident that is actually
        the bad indicator of the traffic
        """
        if destination['is_inner'] == False:
            return destination['ip']
        else:
            return source['ip']

    def insight_query(self, action, query, agent_filter={}):
        """
        Runs a Centra Insight query and can wait for the results
        """

        api_endpoint = "/api/v3.0/agents/query"

        # Raise an error if trying to use an unsupported action value
        if action not in ["run", "preview_selection", "abort"]:
            raise ValueError("Unsupported action. Must be: run, preview_selection, or abort")

        # Build the post payload
        data = {
            "action": action,
            "filter": agent_filter,
            "query": query
        }

        response = self.session.post(f"https://{self.management_url}{api_endpoint}", data=json.dumps(data))
        if response.status_code == 200:
            response_data = response.json()
            return response_data['id']
        else:
            return None

    def insight_query_info(self, query_id, status_only=False):
        """
        Returns information about the query ID
        Important for determining if a query is finished or not
        status_only will just return the current status
        if not set this will return the entire response from the API
        """

        api_endpoint = f"/api/v3.0/agents/query/{query_id}"

        response = self.session.get(f"https://{self.management_url}{api_endpoint}")
        if response.status_code == 200:
            response_data = response.json()

            if status_only:
                return response_data['status']
            else:
                return response_data
        else:
            return None


    def insight_query_results(self, query_id, limit=20, page=0):
        """
        Fetches the result of a completed Insight query
        """

        # Set the default value for to if not overridden
        offset = limit * page

        # Create an empty result set
        results = []

        api_endpoint = f"/api/v3.0/agents/query/{query_id}/results?limit={limit}&offset={offset}"

        response = self.session.get(f"https://{self.management_url}{api_endpoint}")
        if response.status_code == 200:
            response_data = response.json()
            results += response_data['objects']

            # Page if necessary
            if page < round(response_data['total_count']/limit):
                results += self.insight_query_results(query_id, page=response_data['current_page'])

            return results
        else:
            return None
        

        
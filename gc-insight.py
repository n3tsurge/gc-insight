import json
import logging
import yaml
import time
import logging
from pyaml_env import parse_config
from argparse import ArgumentParser
from guardicore.centra import CentraAPI


def load_config(path="config.yml"):
    """
    Loads the configuration file for the application
    and returns a configuration object for consumption in
    other areas
    """
    config_error = False
    config = parse_config(path)

    return config


def execute_query(centra_api, query=None, query_id=None):

    query_results = None
    
    if query_id and not query:
        query_results = centra.insight_query_results(query_id)

    if query:
        query_id = centra.insight_query("run", query, agent_filter={"os": ["Windows"]})

        # Make sure the query executed successfully
        if query_id:
            query_status = None

            # Wait for the query to finish
            while query_status != "DONE":
                query_status = centra.insight_query_info(query_id, status_only=True)
                if query_status == "DONE":
                    break

                logging.info(f"Waiting for query {query_id} to finish...current status {query_status}")            
                time.sleep(10)
            
            query_results = centra.insight_query_results(query_id)

    return query_results


if __name__ == "__main__":
    # Set the logging format
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    
    # Parse script parameters
    parser = ArgumentParser()
    parser.add_argument('--config', help="The path to the configuration file", default="config.yml", required=False)
    parser.add_argument('--query', help="The OS Query you want to run", required=False)
    parser.add_argument('--query-id', help="Fetch the results from a previous query ID", required=False)
    args = parser.parse_args()

    # Load the configuration
    config = load_config(path=args.config)

    # Authenticate to Guardicore
    logging.info("Authenticating to Guardicore")
    centra = CentraAPI(management_url=config['guardicore']['management_url'])
    
    try:
        centra.authenticate(username=config['guardicore']['username'], password=config['guardicore']['password'])
    except Exception as e:
        logging.error(e)
        exit(1)

    results = None
    if args.query_id:
        results = execute_query(centra, query_id=args.query_id)
    elif args.query:
        results = execute_query(centra, query=args.query)
    else:
        for job in config['jobs']:
            print(job)

    print(results)
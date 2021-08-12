import json
import logging
import yaml
import time
import logging
import csv
import datetime
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


def output_csv(job_name, data):
    """
    Sends the JSON results to a CSV
    """

    # Get todays date in UTC
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    logging.info(f"Writing {len(data)} results to {job_name}-{now}.csv")

    with open(f"{job_name}-{now}.csv", 'w', newline='') as f:
        writer = csv.writer(f)

        index = 0
        for record in data:
            if index == 0:
                header = record.keys()
                writer.writerow(header)
                index += 1

            writer.writerow(record.values())
        f.close()


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
    parser.add_argument('--job-name', help="The job name you want to run manually", required=False)
    parser.add_argument('--csv', help="Output the results to a CSV", required=False)
    parser.add_argument('--json', help="Output the results to the screen in JSON format", action="store_true", required=False)
    parser.add_argument('--show-jobs', help="Prints the configured jobs from the config.yml file", action="store_true", required=False)
    parser.add_argument('--gc-timeout', help="How many seconds to wait for an Guardicore Insight query to finish before giving up", required=False)
    args = parser.parse_args()

    # Load the configuration
    config = load_config(path=args.config)

    # Print the jobs available to run based on the configuratio
    # then exit the program
    if args.show_jobs:
        for job in config['jobs']:
            job_config = config['jobs'][job]
            logging.info(f"job_name={job}, query={job_config['query']}, outputs={job_config['output']}, enabled={job_config['enabled']}")
        exit()

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

    elif args.job_name:
        job = [config['jobs'][j] for j in config['jobs'] if j == args.job_name][0]
        results = execute_query(centra, query=job['query'])

        if 'csv' in job['output']:
            output_csv(args.job_name, results)
        
        if 'stdout' in job['output']:
            print(json.dumps(results, indent=4))

    else:
        # Get active jobs
        jobs = config['jobs']
        for job in jobs:
            job_name = job
            job = jobs[job_name]
            if job['enabled']:
                logging.info(f"Running job {job_name}.")
                results = execute_query(centra, query=job['query'])

                if 'csv' in job['output']:
                    output_csv(job_name, results)
            
                if 'stdout' in job['output']:
                    print(json.dumps(results, indent=4))
            else:
                logging.info(f"Skipping {job_name} as it is currently disabled.")

    exit()

    logging.info(f"Writing {len(results)} to CSV file")
    if args.csv:
        
        # If pulling from a job name output to the CSV 
        # using the job name as the prefix for the file
        # if not use the value defined in --csv filename
        if args.job_name:
            output_csv(args.job_name, results)
        else:
            output_csv(args.csv, results)

    if args.json:
        print(json.dumps(results, indent=4))

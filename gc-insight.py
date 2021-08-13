import json
import logging
import yaml
import time
import logging
import csv
import datetime
from getpass import getpass
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

    return query_results, query_id


def manual_label_agents(args, query_id, agent_count):
    """
    Labels agents based on the result of a Centra Query
    """

    if args.label_agents:
        if args.label_key:
            if args.label_value:
                
                if agent_count > 0:
                    result = centra.insight_label_agents(query_id, args.label_key, args.label_value, action="add_to_label")
                    if result:
                        logging.info(f"Labeled {result['added_to_label_count']} agents with the label {args.label_key}: {args.label_value}")
                else:
                    logging.info(f"Skipping labeling, query returned 0 agents.")
            else:
                logging.error("Must define the --label-value flag to assign labels")
                exit(1)
        else:
            logging.error("Must define the --label-key flag to assign labels")
        exit(1)
    return


def automatic_label_agents(query_id, agent_count, label_key, label_value):
    """
    Labels agents based on the result of a Centra Query
    """
    
    if agent_count > 0:
        result = centra.insight_label_agents(query_id, label_key, label_value, action='add_to_label')
        if result:
            logging.info(
                f"Labeled {result['added_to_label_count']} agents with the label {label_key}:{label_value}")
    else:
        logging.info("Skipping labeling, query returned 0 agents.")
    return


def run_job(job_name, job_config):
    """
    Runs the specified job from the config
    """

    logging.info(f"Running job {job_name}")
    results, query_id = execute_query(centra, query=job['query'])

    if 'csv' in job['output']:
        output_csv(job_name, results)
    
    if 'stdout' in job['output']:
        logging.info(f"Displaying results for job {job_name}:")
        print(json.dumps(results, indent=4))

    # If the job calls to label the agents, perform the labeling
    if 'label' in job:
        label_config = job['label']
        automatic_label_agents(query_id, len(results), label_config['key'], label_config['value'])

    return


def output_results(args, results):
    """
    Outputs the results based on what parameters were passed to the script
    """

    if args.csv:
        # If pulling from a job name output to the CSV 
        # using the job name as the prefix for the file
        # if not use the value defined in --csv filename
        if args.job_name:
            output_csv(args.job_name, results)
        else:
            output_csv(args.csv, results)

    if args.json:
        logging.info(f"Displaying results:")
        
        with open(f"results.json", 'w') as f:
            f.write(json.dumps(results))
            f.close()

    if not args.csv and not args.json:
        logging.info(f"Displaying results:")
        print(json.dumps(results, indent=4))


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
    parser.add_argument('--csv', help="Output the results to a CSV, value is filename before extension", required=False)
    parser.add_argument('--json', help="Output the results to the screen in JSON format, value is filename before extension ", required=False)
    parser.add_argument('--show-jobs', help="Prints the configured jobs from the config.yml file", action="store_true", required=False)
    parser.add_argument('--gc-timeout', help="How many seconds to wait for an Guardicore Insight query to finish before giving up", required=False)
    parser.add_argument('--label-agents', help="Tells the tool to label the agents in the result set of the query", action="store_true", required=False)
    parser.add_argument('--label-key', help="The key for the label", required=False)
    parser.add_argument('--label-value', help="The value for the label", required=False)
    parser.add_argument('-u', '--user', help="Guardicore username", required=False)
    parser.add_argument('-p', '--password', help="Prompt for the Guardicore password", required=False, action="store_true")
    args = parser.parse_args()

    # Load the configuration
    config = load_config(path=args.config)

    if args.user:
        config['guardicore']['username'] = args.user

    if args.password:
        config['guardicore']['password'] = getpass(prompt="Password: ")


    # Print the jobs available to run based on the configuratio
    # then exit the program
    if args.show_jobs:
        print(json.dumps(config['jobs'], indent=4))
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

    # If the user is looking up a past query pull the results using that specific query_id
    if args.query_id:
        results, query_id = execute_query(centra, query_id=args.query_id)
        manual_label_agents(args, query_id, len(results))
        output_results(args, results)

    # If the user has defined a customer query, run that query
    elif args.query:
        results, query_id = execute_query(centra, query=args.query)
        manual_label_agents(args, query_id, len(results))
        output_results(args, results)

    # If the user has defined a specific configured job by name run that job
    elif args.job_name:
        job = [config['jobs'][j] for j in config['jobs'] if j == args.job_name][0]
        run_job(args.job_name, job)

    # If running the tool without parameters run all jobs based on the config.yml file
    else:
        # Get active jobs
        jobs = config['jobs']
        for job in jobs:
            job_name = job
            job = jobs[job_name]
            if job['enabled']:
                run_job(job_name, job)
            else:
                logging.info(f"Skipping {job_name} as it is currently disabled.")  
    

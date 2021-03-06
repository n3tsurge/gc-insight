# Guardicore Insight Command Line Tool

The Guardicore Centra UI Insight plugin only lets Insight Queries run at a 4 hour minimum interval.  This tool allows external schedules to run a query on any interval and fetch the results.  It supports outputting the results to multiple different formats for consumption by other tools.

## Features

- [x] Run multiple queries based on a standard configuration in `config.yml`
- [x] Run a single job via the job name and its configuration in `config.yml`
- [x] Run an ad-hoc query using `--query`
- [x] Label assets with `--label-agent` and `--label-key` and `--label-value`
- [x] Output to CSV
- [x] Output to JSON
- [x] Output to stdout
- [ ] Output to Elasticsearch
- [ ] Output to Memcached

## Getting Starting

1. Clone the repository
2. `pip install pipenv`
3. `pipenv install`
4. Add your jobs to `config.yaml`
5. `pipenv run python gc-insight.py`
6. Win

## Parameters

```text
$ pipenv run python .\gc-insight.py -h
usage: gc-insight.py [-h] [--config CONFIG] [--query QUERY]
                     [--query-id QUERY_ID] [--job-name JOB_NAME] [--csv CSV]
                     [--json JSON] [--show-jobs] [--gc-timeout GC_TIMEOUT]
                     [--label-agents] [--label-key LABEL_KEY]
                     [--label-value LABEL_VALUE]

optional arguments:
  -h, --help                  show this help message and exit
  --config CONFIG             The path to the configuration file
  --query QUERY               The OS Query you want to run
  --query-id QUERY_ID         Fetch the results from a previous query ID
  --job-name JOB_NAME         The job name you want to run manually
  --csv CSV                   Output the results to a CSV, value is filename before extension
  --json JSON                 Output the results to the screen in JSON format, value is filename before extension
  --show-jobs                 Prints the configured jobs from the config.yml file
  --gc-timeout GC_TIMEOUT     How many seconds to wait for an Guardicore Insight query to finish before giving up
  --label-agents              Tells the tool to label the agents in the result set of the query
  --label-key LABEL_KEY       The key for the label
  --label-value LABEL_VALUE   The value for the label
```

## Defining Jobs

Jobs are defined in yaml blocks like below

```yaml
zscaler-status:
  enabled: true
  query: "SELECT * FROM services WHERE display_name in ('ZSAService','ZSATunnel') AND status in ('STOPPED','STOPPING')"
  timeout: 300
  label:
    key: Zscaler Agent Status
    value: Stopped
  output:
    csv:
    stdout:
```

## Outputs

Outputs determine what to do with the results from the query, they can be sent to `elasticsearch`, `csv`, `json` or just to `stdout`

### Output configuration

Some outputs require additional configuration to connect to other systems

```yaml
outputs:
  elasticsearch:
     hosts: ["localhost:9200"]
     use_tls: true
     auth_method: "api"
     username: ""
     password: ""
```

## Examples

### Running an ad-hoc query

```text
pipenv run python .\gc-insight.py --query "SELECT * FROM services" --csv service-status
```

### Getting the results of a previous query

```text
pipenv run python .\gc-insight.py --query-id c51810f9-d6ae-40e8-8fde-de1965e4dfb6 --json
```

### Running a specific job from the config

```text
pipenv run python .\gc-insight.py --job-name service-status
```

## Warranty & Support

I am not responsible if you break your system with this script. Usage is up to your own risk appetite.  This software has no warranty.

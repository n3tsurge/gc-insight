# Guardicore Insight Command Line Tool

The Guardicore Centra UI Insight plugin only lets Insight Queries run at a 4 hour minimum interval.  This tool allows external schedules to run a query on any interval and fetch the results.  It supports outputting the results to multiple different formats for consumption by other tools.

## Getting Starting

1. Clone the repository
2. `pipenv install`
3. Add your jobs to `config.yaml`
4. `pipenv run python gc-insight.py`
5. Win

## Defining Jobs

Jobs are defined in yaml blocks like below

```yaml
sentinelone-status:
  query: "SELECT * FROM services WHERE name in ('Sentinel Agent')"
  output:
    elasticsearch:
      enabled: true
      index: "sentinelone-service-status"
    stdout:
```

## Outputs
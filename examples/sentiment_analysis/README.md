# Sentiment Analysis

This model labels text as positive or negative and assigns it a value between 0 and 1.

## inferex.yaml

The inferex.yaml file specifies server resources to limit the deployment to. E.g.,

```
project:
  name: SentimentAnalysis

scaling:
  cpu: "1000m"
  memory: "5G"
  replicas: 1
```

The above config will use the server defaults of 1 CPU (or 1000 mili-cpu) and 5 gigabytes of memory.
For deployments with a heavier workload it is recommended to allocate more resources accordingly.

Test the inference with a curl command:

```
curl -d '{"text": "Pied piper is the best thing to happen to tech in the last decade."}' -H "Content-Type: application/json" -X POST <DEPLOYMENT_URL>
```

Should produce `{"label":"POSITIVE","score":0.9963924288749695}`

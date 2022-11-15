# Text Generation

Given a text prompt, uses a TextGenerationPipeline to generate a body of text.

After deploying this project you may query the model as below:

```
$ curl -d '{"text": "What is 42 ?"}' -H "Content-Type: application/json" -X POST <DEPLOYMENT URL>
{"generated_text": "The meaning of life."} *
```

* This is merely an example and the model cannot currently compute the answer to the meaning of life.
** The model may require two POST requests before output is returned, in order to "warm up" first.

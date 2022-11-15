# Whisper

Takes a URI to a file (.mp3) with audio and transcribes the audio into a text output.

```
$ curl -H "Content-Type: application/json" -X POST -d '{"url": "https://drive.google.com/uc?export=view&id=1Z1s2-XA4AW5RCxjgCTmq3nRfFsBYyfoP"}' <WHISPER DEPLOYMENT URL>
{"text":"(something hilarious)"}
```

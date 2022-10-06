
import requests
import whisper
import inferex


# Load the model
model = whisper.load_model("base", device="cpu")


@inferex.pipeline(name="whisper")
def whisper(payload: dict) -> dict:

    # Download the audio file from the payload
    url = payload['url']
    file_path = url.split('/')[-1]
    print(url, file_path)

    r = requests.get(url, allow_redirects=True)
    print(r)

    with open(file_path, 'wb') as file:
        file.write(r.content)

    # Transcribe the audio file
    result = model.transcribe(file_path)
    print({"text": result["text"]})

    return {"text": result["text"]}


whisper({"url": "https://basicenglishspeaking.com/wp-content/uploads/audio/QA/QA-01.mp3"})

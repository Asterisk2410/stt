### Code for English audio to French text Translation
# We first process the audio and detect the language if english we get the text in english then translate the text to French(audio > transcript > detect > translate > text output)

import os
import time
import pyaudio
from googletrans import Translator
from langdetect import detect
from google.oauth2 import service_account
from google.cloud import speech

# Path to your Google Cloud service account key file
client_file = "speech_to_text_cred.json"
credentials = service_account.Credentials.from_service_account_file(client_file)
speech_client = speech.SpeechClient(credentials=credentials)

# Audio recording parameters
RATE = 24000
CHUNK = int(RATE / 10)  # 100ms

def record_audio():
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    print("Listening...")

    frames = []

    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            audio_content = b''.join(frames)
            if len(frames) >= RATE // CHUNK * 5:  # Process every 5 seconds of audio
                process_audio(audio_content)
                frames = []  # Reset frames for the next chunk
    except KeyboardInterrupt:
        print("Stopped listening.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

def process_audio(audio_content):
    transcript = transcribe_audio(audio_content)
    print(f"Transcript: {transcript}")

    if transcript.strip():
        detected_language = detect(transcript)
        print(f"Detected Language: {detected_language}")

        if detected_language == 'en':
            translated_text = translate_text(transcript, 'fr')
            print(f"Translated text (en to fr): {translated_text}")
        elif detected_language == 'fr':
            translated_text = translate_text(transcript, 'en')
            print(f"Translated text (fr to en): {translated_text}")
        else:
            print("Unsupported language detected")
    else:
        print("No text detected.")

def transcribe_audio(audio_content):
    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="en-US",  # Default language for transcription
    )

    response = speech_client.recognize(config=config, audio=audio)
    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript
        confidence += result.alternatives[0].confidence
    return transcript

def translate_text(text, dest_language):
    translator = Translator()
    translation = translator.translate(text, dest=dest_language)
    return translation.text

if __name__ == "__main__":
    record_audio()

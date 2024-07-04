import os
import io
import time
import pyaudio
from googletrans import Translator
from langdetect import detect
from google.oauth2 import service_account
from google.cloud import speech

# Path to your Google Cloud service account key file
client_file= "speech_to_text_cred.json"
credentials = service_account.Credentials.from_service_account_file(client_file)
speech_client = speech.SpeechClient(credentials=credentials)

# Audio recording parameters
RATE = 24000
CHUNK = int(RATE / 10)  # 100ms
RECORD_SECONDS = 5  # Timeout of 5 seconds

def record_audio():
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    print("Listening...")

    frames = []
    start_time = time.time()

    while True:
        data = stream.read(CHUNK)
        frames.append(data)
        if time.time() - start_time > RECORD_SECONDS:
            break

    print("Recording stopped.")
    stream.stop_stream()
    stream.close()
    p.terminate()
    print(b''.join(frames))
    return b''.join(frames)

def audio_file():
    audio_file = r"russian audio.mp3"
    with io.open(audio_file, 'rb') as audio_file:
        content = audio_file.read()
    return content

def transcribe_audio(audio_content, language_code):
    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=RATE,
        language_code=language_code,  # Default language for transcription
    )

    response = speech_client.recognize(config=config, audio=audio)
    transcript = ""
    confidence = 0.0
    print("response:", response)

    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript
        confidence = result.alternatives[0].confidence
    return transcript, confidence

def translate_text(text, dest_language):
    translator = Translator()
    translation = translator.translate(text, dest=dest_language)
    # print(f"Translated Text: {translation.text}")
    return translation.text

def main():
    # audio_content = record_audio()
    audio_content = audio_file()
    transcript, confidence = transcribe_audio(audio_content, "ar-AE")
    # print(f"Transcript: {transcript}")
    
    if confidence < 0.85:
        transcript, confidence = transcribe_audio(audio_content, "ru-RU")

    if transcript.strip():
        # transcript = "Bonjour comment vas-tu Python est génial"
        detected_language = detect(transcript)
        print(f"Detected Language: {detected_language}")

        if detected_language == 'ar':
            translated_text = translate_text(transcript, 'ru')
            print(f"Output Text: {translated_text}")
        elif detected_language == 'ru':
            translated_text = translate_text(transcript, 'ar')
            print(f"Output Text: {translated_text}")
        else:
            print("Unsupported language detected")
            return
    else:
        print("No text detected.")


if __name__ == "__main__":
    main()
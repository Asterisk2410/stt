import speech_recognition as sr
from googletrans import Translator
from langdetect import detect
import os, io
# from dotenv import load_dotenv
from google.oauth2 import service_account
from google.cloud import speech

client_file = "speech_to_text_cred.json"
credentials = service_account.Credentials.from_service_account_file(client_file)
client = speech.SpeechClient(credentials=credentials)

with io.open('audio.wav', 'rb') as audio_file:
    content = audio_file.read()
    audio = speech.RecognitionAudio(content=content)

config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=16000,
    language_code="fr-FR",
)

response = client.recognize(config=config, audio=audio)

print("Transcript: {}".format(response.results[0].alternatives[0].transcript))

def speech_to_text(recognizer, microphone):
    with microphone as source:
        print("Listening for up to 5 seconds...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
        except sr.WaitTimeoutError:
            print("Listening timed out while waiting for phrase to start")
            return None
    
    print("Recognizing...")
    try:
        text = recognizer.recognize_google_cloud(audio)
        print(f"Recognized Text: {text}")
        return text
    except sr.UnknownValueError:
        print("Could not understand the audio")
        return None
    except sr.RequestError as e:
        print(f"Error with the Google Speech Recognition service: {e}")
        return None

def translate_text(text, dest_language):
    translator = Translator()
    translation = translator.translate(text, dest=dest_language)
    print(f"Translated Text: {translation.text}")
    return translation.text

def main():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    text = speech_to_text(recognizer, microphone)
    if text:
        detected_language = detect(text)
        print(f"Detected Language: {detected_language}")

        if detected_language == 'en':
            dest_language = 'fr'
        elif detected_language == 'fr':
            dest_language = 'en'
        else:
            print("Unsupported language detected")
            return

        translated_text = translate_text(text, dest_language)
        print(f"Output Text: {translated_text}")

if __name__ == "__main__":
    main()

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
    transcript, confidence = transcribe_audio(audio_content, "en-US")
    
    if confidence < 0.7:
        print("Low confidence detected, retrying with French configuration.")
        transcript, confidence = transcribe_audio(audio_content, "fr-FR")

    if transcript.strip():
        try:
            detected_language = detect(transcript)
            print(f"Detected Language: {detected_language}")
        except Exception as e:
            print(f"Language detection failed: {e}")
            return

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

def transcribe_audio(audio_content, language_code):
    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code,
    )

    response = speech_client.recognize(config=config, audio=audio)
    transcript = ""
    confidence = 0.0

    if response.results:
        for result in response.results:
            transcript += result.alternatives[0].transcript
            confidence = result.alternatives[0].confidence
            
        print(transcript, confidence)
        billing = response.total_billed_time.seconds
        print(f"Billing: {billing} seconds")
    return transcript, confidence

def translate_text(text, dest_language):
    translator = Translator()
    translation = translator.translate(text, dest=dest_language)
    return translation.text

if __name__ == "__main__":
    record_audio()

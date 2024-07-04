import base64
import io
from flask import Flask, request, jsonify, render_template
from googletrans import Translator
from langdetect import detect
from google.oauth2 import service_account
from google.cloud import speech

app = Flask(__name__)

# Path to your Google Cloud service account key file
client_file = "speech_to_text_cred.json"
credentials = service_account.Credentials.from_service_account_file(client_file)
speech_client = speech.SpeechClient(credentials=credentials)

RATE = 48000  # Set the sample rate to 24000

def transcribe_audio(audio_content, language_code):
    with io.BytesIO(audio_content) as audio:
        audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
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
    return transcript, confidence

def translate_text(text, dest_language):
    translator = Translator()
    translation = translator.translate(text, dest=dest_language)
    return translation.text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_audio', methods=['POST'])
def process_audio():
    try:
        audio_file = request.files['file']
        audio_content = audio_file.read()
        if audio_file.filename == '':
            return jsonify({"error": "No audio file selected"})

        # Ensure the audio file type is supported (audio/webm;codecs=opus)
        if audio_file.content_type == 'audio/webm;codecs=opus':
            
            transcript, confidence = transcribe_audio(audio_content, "en-US")

            if confidence < 0.7:
                transcript, confidence = transcribe_audio(audio_content, "ja-JP")

            if transcript.strip():
                detected_language = detect(transcript)
                if detected_language == 'en':
                    translated_text = translate_text(transcript, 'ja')
                elif detected_language == 'ja':
                    translated_text = translate_text(transcript, 'en')
                else:
                    return jsonify({"error": "Unsupported language detected"})
            else:
                return jsonify({"error": "No text detected"})

            return jsonify({"transcript": transcript, "translation": translated_text})

        else:
            return jsonify({'error': 'Unsupported file type'})

    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        return jsonify({'error': f'Error processing audio: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True)

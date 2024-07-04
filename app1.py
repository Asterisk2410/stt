import azure.cognitiveservices.speech as speechsdk
from googletrans import Translator
from langdetect import detect

def speech_to_text(api_key, region):
    speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)
    
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)
    
    print("Listening for up to 5 seconds...")
    result = recognizer.recognize_once_async().get()
    
    # Checks the result.
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print(f"Recognized Text: {result.text}")
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized")
        return None
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Speech Recognition canceled: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(f"Error details: {cancellation_details.error_details}")
        return None

def translate_text(text, dest_language):
    translator = Translator()
    translation = translator.translate(text, dest=dest_language)
    # print(f"Translated Text: {translation.text}")
    return translation.text

def main():
    # Replace with your Azure Speech API key and region
    api_key = "ff542d4a97f340d4ae9faa685afab149"
    region = "eastus"

    text = speech_to_text(api_key, region)
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

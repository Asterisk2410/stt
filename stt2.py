# import eventlet
# eventlet.monkey_patch()
# from flask import Flask, render_template
# from flask_socketio import SocketIO, emit
# import io
# import queue
# import time
# import threading
# from google.cloud import speech
# from google.oauth2 import service_account
# import pyaudio
# import re
# from googletrans import Translator


# app = Flask(__name__)

# socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# # Audio recording parameters
# STREAMING_LIMIT = 240000  # 4 minutes
# SAMPLE_RATE = 16000
# CHUNK_SIZE = int(SAMPLE_RATE / 10)  # 100ms
# RATE = 48000

# client_file = "speech_to_text_cred.json"
# credentials = service_account.Credentials.from_service_account_file(client_file)
# speech_client = speech.SpeechClient(credentials=credentials)
# # translate_client = translate.Client(credentials=credentials)

# def get_current_time():
#     """Return Current Time in MS."""
#     return int(round(time.time() * 1000))


# class ResumableMicrophoneStream:
#     def __init__(self, rate, chunk_size):
#         self._rate = rate
#         self.chunk_size = chunk_size
#         self._num_channels = 1
#         self._buff = queue.Queue()
#         self.closed = True
#         self.start_time = get_current_time()
#         self.restart_counter = 0
#         self.audio_input = []
#         self.last_audio_input = []
#         self.result_end_time = 0
#         self.is_final_end_time = 0
#         self.final_request_end_time = 0
#         self.bridging_offset = 0
#         self.last_transcript_was_final = False
#         self.new_stream = True
#         self._audio_interface = pyaudio.PyAudio()
#         self._audio_stream = self._audio_interface.open(
#             format=pyaudio.paInt16,
#             channels=self._num_channels,
#             rate=self._rate,
#             input=True,
#             frames_per_buffer=self.chunk_size,
#             stream_callback=self._fill_buffer,
#         )

#     def __enter__(self):
#         self.closed = False
#         return self

#     def __exit__(self, type, value, traceback):
#         self._audio_stream.stop_stream()
#         self._audio_stream.close()
#         self.closed = True
#         self._buff.put(None)
#         self._audio_interface.terminate()

#     def _fill_buffer(self, in_data, *args, **kwargs):
#         self._buff.put(in_data)
#         return None, pyaudio.paContinue

#     def generator(self):
#         while not self.closed:
#             data = []

#             if self.new_stream and self.last_audio_input:
#                 chunk_time = STREAMING_LIMIT / len(self.last_audio_input)
#                 if chunk_time != 0:
#                     if self.bridging_offset < 0:
#                         self.bridging_offset = 0

#                     if self.bridging_offset > self.final_request_end_time:
#                         self.bridging_offset = self.final_request_end_time

#                     chunks_from_ms = round(
#                         (self.final_request_end_time - self.bridging_offset)
#                         / chunk_time
#                     )

#                     self.bridging_offset = round(
#                         (len(self.last_audio_input) - chunks_from_ms) * chunk_time
#                     )

#                     for i in range(chunks_from_ms, len(self.last_audio_input)):
#                         data.append(self.last_audio_input[i])

#                 self.new_stream = False

#             chunk = self._buff.get()
#             self.audio_input.append(chunk)

#             if chunk is None:
#                 return
#             data.append(chunk)
#             while True:
#                 try:
#                     chunk = self._buff.get(block=False)

#                     if chunk is None:
#                         return
#                     data.append(chunk)
#                     self.audio_input.append(chunk)

#                 except queue.Empty:
#                     break

#             yield b"".join(data)


# def listen_print_loop(responses, stream, target_language):
#     for response in responses:
#         if get_current_time() - stream.start_time > STREAMING_LIMIT:
#             stream.start_time = get_current_time()
#             break

#         if not response.results:
#             continue

#         result = response.results[0]

#         if not result.alternatives:
#             continue
        
#         # check if we can add confidence as a query for swapping languages
#         print('Result', result)
#         print('Response', responses)
        
#         transcript = result.alternatives[0].transcript

#         result_seconds = 0
#         result_micros = 0

#         if result.result_end_time.seconds:
#             result_seconds = result.result_end_time.seconds

#         if result.result_end_time.microseconds:
#             result_micros = result.result_end_time.microseconds

#         stream.result_end_time = int((result_seconds * 1000) + (result_micros / 1000))

#         corrected_time = (
#             stream.result_end_time
#             - stream.bridging_offset
#             + (STREAMING_LIMIT * stream.restart_counter)
#         )

#         if result.is_final:
#             translation = translate_text(transcript, target_language)
#             socketio.emit('translated_text', {'transcript': transcript, 'translation': translation})
#             stream.is_final_end_time = stream.result_end_time
#             stream.last_transcript_was_final = True

#             if re.search(r"\b(exit|quit)\b", transcript, re.I):
#                 stream.closed = True
#                 break
#         else:
#             stream.last_transcript_was_final = False


# def translate_text(text, target_language):
#     translator = Translator()
#     translation = translator.translate(text, dest=target_language)
#     return translation.text
    
#     # result = translate_client.translate(text, target_language=target_language)
#     # return result['translatedText']


# @app.route('/')
# def index():
#     return render_template('index.html')


# @socketio.on('start_audio_stream')
# def start_audio_stream(data):
#     target_language = 'fr-FR'
#     mic_manager = ResumableMicrophoneStream(SAMPLE_RATE, CHUNK_SIZE)
#     with mic_manager as stream:
#         while not stream.closed:
#             stream.audio_input = []
#             audio_generator = stream.generator()

#             requests = (
#                 speech.StreamingRecognizeRequest(audio_content=content)
#                 for content in audio_generator
#             )

#             streaming_config = speech.RecognitionConfig(
#                 encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
#                 sample_rate_hertz=RATE,
#                 language_code='en-US',
#             )
            
#             responses = speech_client.streaming_recognize(streaming_config, requests)
#             listen_print_loop(responses, stream, target_language)

#             if stream.result_end_time > 0:
#                 stream.final_request_end_time = stream.is_final_end_time
#             stream.result_end_time = 0
#             stream.last_audio_input = []
#             stream.last_audio_input = stream.audio_input
#             stream.audio_input = []
#             stream.restart_counter += 1

#             if not stream.last_transcript_was_final:
#                 stream.new_stream = True


# if __name__ == "__main__":
#     socketio.run(app, debug=True)


import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import io
import queue
import time
import threading
from googletrans import Translator
from google.cloud import speech, translate_v2 as translate
from google.oauth2 import service_account

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Google Cloud credentials
credentials = service_account.Credentials.from_service_account_file('speech_to_text_cred.json')


# Audio recording parameters
STREAMING_LIMIT = 240000  # 4 minutes
SAMPLE_RATE = 48000
CHUNK_SIZE = int(SAMPLE_RATE / 10)  # 100ms

def get_current_time() -> int:
    """Return Current Time in MS."""
    return int(round(time.time() * 1000))

class ResumableMicrophoneStream:
    def __init__(self, rate, chunk_size):
        self._rate = rate
        self.chunk_size = chunk_size
        self._num_channels = 1
        self._buff = queue.Queue()
        self.closed = True
        self.start_time = get_current_time()
        self.restart_counter = 0
        self.audio_input = []
        self.last_audio_input = []
        self.result_end_time = 0
        self.is_final_end_time = 0
        self.final_request_end_time = 0
        self.bridging_offset = 0
        self.last_transcript_was_final = False
        self.new_stream = True

    def __enter__(self):
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self.closed = True
        self._buff.put(None)

    def _fill_buffer(self, in_data):
        self._buff.put(in_data)
        return None

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)

def transcribe_and_translate(audio_generator, target_language='fr'):
    client = speech.SpeechClient(credentials=credentials)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        sample_rate_hertz=SAMPLE_RATE,
        language_code='en-US',
        max_alternatives=1,
    )

    streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)
    
    requests = (speech.StreamingRecognizeRequest(audio_content=content) for content in audio_generator)

    responses = client.streaming_recognize(streaming_config, requests)

    for response in responses:
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue
        
        print('Result', result)
        print('Response', response)
        
        transcript = result.alternatives[0].transcript
        if result.is_final:
            detected_language = 'en'  # Placeholder for actual language detection logic
            translation = translate_text(transcript, target_language) if detected_language == 'en' else transcript
            emit('translated_text', {'transcript': transcript, 'translation': translation})

def translate_text(text, target_language):
    translator = Translator()
    translation = translator.translate(text, dest=target_language)
    return translation.text

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('audio_data')
def handle_audio_data(data):
    if not hasattr(handle_audio_data, 'stream'):
        handle_audio_data.stream = ResumableMicrophoneStream(SAMPLE_RATE, CHUNK_SIZE)
        handle_audio_data.stream.__enter__()

    handle_audio_data.stream._fill_buffer(data)

@socketio.on('start_audio_stream')
def start_audio_stream():
    threading.Thread(target=transcribe_and_translate, args=(handle_audio_data.stream.generator(), 'fr')).start()

@socketio.on('disconnect')
def handle_disconnect():
    if hasattr(handle_audio_data, 'stream'):
        handle_audio_data.stream.__exit__(None, None, None)

if __name__ == "__main__":
    socketio.run(app, debug=True)

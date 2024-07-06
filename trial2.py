import pyaudio
import numpy as np
from transformers import AutoProcessor, SeamlessM4TModel
import torchaudio
import time

# Initialize the processor and model
processor = AutoProcessor.from_pretrained("facebook/hf-seamless-m4t-large")
model = SeamlessM4TModel.from_pretrained("facebook/hf-seamless-m4t-large")

# Define the target sampling rate
target_sampling_rate = 16000

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms
RECORD_SECONDS = 10  # Timeout of 5 seconds

# Function to capture audio from the microphone
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
    print("Recording...")

    while True:
        data = stream.read(CHUNK)
        frames.append(data)
        if time.time() - start_time > RECORD_SECONDS:
            print("timeout.")
            break

    print("Recording stopped.")
    stream.stop_stream()
    stream.close()
    p.terminate()

    audio_data = np.frombuffer(b''.join(frames), dtype=np.int16).astype(np.float32) / 32768.0
    return audio_data

# Record audio from the microphone for a specified duration (e.g., 5 seconds)
audio = record_audio()

# media, original_sampling_rate = torchaudio.load(audio)

if RATE == 16000:
    
    # Process the captured audio sample
    audio_inputs = processor(audios=audio, sampling_rate=target_sampling_rate, return_tensors="pt")

    # Process some English text
    text_inputs = processor(text="Hello, my dog is cute", src_lang="eng", return_tensors="pt")

    # From audio
    output_tokens = model.generate(**audio_inputs, tgt_lang="fra", generate_speech=False, return_intermediate_token_ids=True)
    translated_text_from_audio = processor.decode(output_tokens[0].tolist()[0], skip_special_tokens=True)
    print("Translated text from audio:", translated_text_from_audio)

    # From text
    output_tokens = model.generate(**text_inputs, tgt_lang="fra", generate_speech=False, return_intermediate_token_ids=True)
    translated_text_from_text = processor.decode(output_tokens[0].tolist()[0], skip_special_tokens=True)
    print("Translated text from text:", translated_text_from_text)

else:
    print("Audio sample is not at the target sampling rate. Resampling needed.")

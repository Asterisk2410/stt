import asyncio
import websockets
import soundfile as sf
import numpy as np
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from transformers import pipeline

# Load the Whisper model and processor
model_name = "openai/whisper-large-v3"
processor = WhisperProcessor.from_pretrained(model_name)
model = WhisperForConditionalGeneration.from_pretrained(model_name)

# Create a pipeline for automatic speech recognition and translation
asr_pipeline = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
)

async def transcribe(websocket, path):
    async for message in websocket:
        # Assuming the message is audio data in chunks (raw bytes)
        audio_data = np.frombuffer(message, np.int16)
        
        # Save the audio data to a temporary file
        sf.write("temp.wav", audio_data, samplerate=16000)
        
        # Use the pipeline to transcribe and translate the audio
        result = asr_pipeline("temp.wav")
        transcription = result["text"]
        
        # Optionally, translate the transcription
        translated_text = model.generate(
            processor.tokenizer(transcription, return_tensors="pt").input_ids, 
            forced_bos_token_id=processor.tokenizer.lang_code_to_id["fr"]
        )
        translated_text = processor.tokenizer.batch_decode(translated_text, skip_special_tokens=True)[0]
        
        await websocket.send({
            "transcription": transcription,
            "translation": translated_text
        })

start_server = websockets.serve(transcribe, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

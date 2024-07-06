from transformers import AutoProcessor, SeamlessM4TModel
from datasets import load_dataset
import torchaudio


processor = AutoProcessor.from_pretrained("facebook/hf-seamless-m4t-large")
model = SeamlessM4TModel.from_pretrained("facebook/hf-seamless-m4t-large")


# Load the local audio file
audio_path = r"audio\test.wav"
audio, original_sampling_rate = torchaudio.load(audio_path)

# Resample the audio to 16000 Hz if it's not already at that rate
target_sampling_rate = 16000
if original_sampling_rate != target_sampling_rate:
    resampler = torchaudio.transforms.Resample(orig_freq=original_sampling_rate, new_freq=target_sampling_rate)
    audio = resampler(audio)

# Convert the audio tensor to a numpy array
audio_array = audio.numpy().squeeze()

# Process the resampled audio sample
audio_inputs = processor(audios=audio_array, sampling_rate=target_sampling_rate, return_tensors="pt")

# Process some English text
text_inputs = processor(text="Hello, my dog is cute", src_lang="eng", return_tensors="pt")

# from audio
output_tokens = model.generate(**audio_inputs, tgt_lang="fra", generate_speech=False, return_intermediate_token_ids=True)
translated_text_from_audio = processor.decode(output_tokens[0].tolist()[0], skip_special_tokens=True)
print(translated_text_from_audio)

# from text
output_tokens = model.generate(**text_inputs, tgt_lang="fra", generate_speech=False, return_intermediate_token_ids=True)
translated_text_from_text = processor.decode(output_tokens[0].tolist()[0], skip_special_tokens=True)
print(translated_text_from_text)


# # let's load an audio sample from an Arabic speech corpus
# dataset = load_dataset("arabic_speech_corpus", split="test", streaming=True, trust_remote_code=True)
# audio_sample = next(iter(dataset))["audio"]

# # Determine the sampling rate of the audio sample
# original_sampling_rate = audio_sample["sampling_rate"]

# # Resample the audio to 16000 Hz if it's not already at that rate
# target_sampling_rate = 16000
# if original_sampling_rate != target_sampling_rate:
#     resampler = torchaudio.transforms.Resample(orig_freq=original_sampling_rate, new_freq=target_sampling_rate)
#     audio_array = resampler(torch.tensor(audio_sample["array"]))
# else:
#     audio_array = torch.tensor(audio_sample["array"])
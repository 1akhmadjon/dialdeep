import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoTokenizer, WhisperProcessor, AutomaticSpeechRecognitionPipeline

model = AutoModelForSpeechSeq2Seq.from_pretrained("STT_model")
tokenizer = AutoTokenizer.from_pretrained("STT_model")
processor = WhisperProcessor.from_pretrained("STT_model")
feature_extractor = processor.feature_extractor

forced_decoder_ids = processor.get_decoder_prompt_ids(task="transcribe")
pipe = AutomaticSpeechRecognitionPipeline(model=model, tokenizer=tokenizer, feature_extractor=feature_extractor)

def handle_voice(audio):

    with torch.cuda.amp.autocast():
        text = pipe(audio, return_timestamps=True)["text"]

audio = "incoming_audio/test.mp3"

handle_voice(audio)
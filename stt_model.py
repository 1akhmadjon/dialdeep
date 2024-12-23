import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoTokenizer, WhisperProcessor, AutomaticSpeechRecognitionPipeline
from typing import Dict

MODEL_NAME = "STT_model"

# Загрузка модели
model = AutoModelForSpeechSeq2Seq.from_pretrained(MODEL_NAME)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
processor = WhisperProcessor.from_pretrained(MODEL_NAME)
feature_extractor = processor.feature_extractor

# Проверка доступности устройства
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# Создание пайплайна
pipe = AutomaticSpeechRecognitionPipeline(
    model=model,
    tokenizer=tokenizer,
    feature_extractor=feature_extractor,
    task="transcribe"
)

def transcribe_audio(file_path: str) -> Dict[str, str]:
    """
    Выполняет транскрипцию аудиофайла.

    Параметры:
    file_path (str): Путь к аудиофайлу.

    Возвращает:
    Dict[str, str]: Результат транскрипции, включая текст и таймстемпы.
    """
    # Предобработка аудио

    # Транскрипция
    with torch.amp.autocast("cuda"):
        result = pipe(file_path, return_timestamps=True)

    if not result or "text" not in result:
        raise ValueError("Результат транскрипции некорректен.")

    return result


def save_transcription(result: Dict[str, str], output_path: str) -> None:
    """
    Сохраняет результат транскрипции в файл с проверкой на ключевые слова в названии файла.
    Убирает информацию о временных метках.

    Параметры:
    result (Dict[str, str]): Результат транскрипции.
    output_path (str): Путь к файлу для сохранения.
    file_name (str): Название обрабатываемого файла.
    """
    print(output_path)
    # Format tekshirish
    speaker_role = "operator" if "MIC" in output_path.upper() else "client" if "SPEAKER" in output_path.upper() else "unknown"

    with open(output_path, "w", encoding="utf-8") as f:
        # Asosiy matnni yozish
        f.write(f"Text: {result['text']}\n")

        # Har bir qismni mos ravishda formatlash
        for chunk in result.get("chunks", []):
            text = chunk.get("text", "")

            # Rolni belgilang
            if speaker_role != "unknown":
                f.write(f"{speaker_role}: {text}\n")
            else:
                f.write(f"{text}\n")

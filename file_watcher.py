import os
from watchdog.events import FileSystemEventHandler
from stt_model import transcribe_audio, save_transcription
from text_analysis import analyze_text


class AudioFileHandler(FileSystemEventHandler):
    """
    Обработчик событий для наблюдения за директорией.
    """
    def __init__(self, output_directory: str):
        self.output_directory = output_directory

    def on_created(self, event):
        """
        Обрабатывает событие создания нового файла.
        """
        if event.is_directory or not event.src_path.endswith(".wav"):
            return

        print(f"Обнаружен новый аудиофайл: {event.src_path}")
        self.process_audio_file(event.src_path)

    def process_audio_file(self, file_path: str):
        """
        Processes the new audio file: transcription and analysis.
        """
        try:
            result = transcribe_audio(file_path)

            base_filename = os.path.splitext(os.path.basename(file_path))[0]
            output_path = os.path.join(self.output_directory, f"{base_filename}.txt")

            save_transcription(result, output_path)

            analysis = analyze_text(result['text'])
            print("Text analysis:")
            for key, value in analysis.items():
                print(f" - {key}: {value}")
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

import threading
import time
from pathlib import Path
import asyncio
from collections import defaultdict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import aiofiles

from utils import send_result_to_api


async def merge_transcription_files():
    """
    Объединяет транскрипционные файлы для каждой группы аудиофайлов в один.

    Эта функция сканирует папку с транскрипциями и группирует файлы по их имени (основываясь на 
    первой части имени файла). Если для каждой группы аудиофайлов (определяется по имени 
    файла) присутствуют все необходимые аудиофайлы в папке `incoming_audio`, то транскрипции 
    этих файлов объединяются в один файл в папке `transcriptions/merged`.

    Асинхронно обрабатывает все группы, создавая один выходной файл для каждой группы.
    """

    transcriptions_folder = Path("transcriptions")
    incoming_audio_folder = Path("incoming_audio")
    output_folder = transcriptions_folder / "merged"
    output_folder.mkdir(parents=True, exist_ok=True)

    grouped_files = defaultdict(list)

    for text_file in transcriptions_folder.glob("audio_part_*_*.txt"):
        group_key = "_".join(text_file.stem.split("_")[:3])
        grouped_files[group_key].append(text_file)

    tasks = []
    for group_key, files in grouped_files.items():
        audio_files_exist = all(
            (incoming_audio_folder / (file.stem + ".wav")).exists() for file in files
        )
        if audio_files_exist:
            output_file = output_folder / f"{group_key}_merged.txt"
            tasks.append(write_grouped_files(files, output_file))
        else:
            print(f"Skipping group {group_key}: Not all audio files are present.")

    if tasks:
        await asyncio.gather(*tasks)


async def write_grouped_files(files, output_file):
    """
    Записывает объединенные данные из нескольких файлов в один.

    Эта функция сортирует файлы в порядке их имени, затем асинхронно читает содержимое 
    каждого файла и записывает его в один объединенный файл. Файлы объединяются по 
    порядку их имен.

    Аргументы:
        files (list): Список файлов для объединения.
        output_file (Path): Путь к выходному файлу, в который будет записано содержимое.
    """

    files = sorted(files, key=lambda f: f.stem)
    async with aiofiles.open(output_file, "w", encoding="utf-8") as outfile:
        for file in files:
            async with aiofiles.open(file, "r", encoding="utf-8") as infile:
                content = await infile.read()
                await outfile.write(content + "\n")
    print(f"Merged: {output_file}")


def all_files_ready():
    """
    Проверяет, готовы ли все файлы для объединения.

    Эта функция проверяет для каждой группы транскрипционных файлов наличие 
    соответствующих аудиофайлов в папке `incoming_audio`. Если для каждой группы 
    отсутствует хотя бы один аудиофайл, функция возвращает False. В противном случае 
    возвращает True, что означает, что все файлы готовы для объединения.

    Возвращает:
        bool: True, если все аудиофайлы присутствуют, иначе False.
    """

    transcriptions_folder = Path("transcriptions")
    incoming_audio_folder = Path("incoming_audio")

    grouped_files = defaultdict(list)
    for text_file in transcriptions_folder.glob("audio_part_*_*.txt"):
        group_key = "_".join(text_file.stem.split("_")[:2])
        grouped_files[group_key].append(text_file)

    for group_key, files in grouped_files.items():
        audio_files_exist = all(
            (incoming_audio_folder / (file.stem + ".wav")).exists() for file in files
        )
        if not audio_files_exist:
            return False
    return True


class TranscriptionFileHandler(FileSystemEventHandler):
    """
    Обработчик событий файлов для отслеживания изменений в папке транскрипций.

    Этот класс обрабатывает события создания новых транскрипционных файлов в папке 
    `transcriptions`. Когда новый файл транскрипции создается, вызывается метод 
    `handle_event()`, который проверяет, готовы ли все аудиофайлы, и если да, выполняет 
    объединение транскрипционных файлов в один и отправку результата на API.

    Атрибуты:
        loop (asyncio.AbstractEventLoop): Событийный цикл для асинхронной обработки.
        last_call_time (float): Время последнего вызова метода, используется для дебаунса.
        debounce_interval (int): Интервал в секундах для дебаунса повторных вызовов.
        lock (asyncio.Lock): Асинхронный замок для предотвращения одновременного выполнения.
    """

    def __init__(self, loop):
        self.loop = loop
        self.last_call_time = 0
        self.debounce_interval = 3  # seconds
        self.lock = asyncio.Lock()

    def on_created(self, event):
        """
        Обрабатывает событие создания нового файла.
    
        Этот метод срабатывает, когда в папке транскрипций появляется новый файл. Он проверяет, 
        является ли файл транскрипцией (с расширением `.txt` и названием, начинающимся с 
        `audio_part_`). Если условие выполняется, запускается асинхронная обработка события 
        через `handle_event()`.
    
        Аргументы:
            event (FileSystemEvent): Событие, которое вызвало метод.
        """

        file_path = Path(event.src_path)
        current_time = time.time()

        if current_time - self.last_call_time < self.debounce_interval:
            print("Debouncing repeated calls.")
            return
        self.last_call_time = current_time

        if file_path.suffix == ".txt" and file_path.stem.startswith("audio_part_"):
            print(f"New transcription file detected: {file_path}")
            asyncio.run_coroutine_threadsafe(self.handle_event(), self.loop)

    async def handle_event(self):
        """
        Асинхронно обрабатывает событие, проверяя готовность всех файлов и объединяя транскрипции.
    
        Этот метод проверяет, готовы ли все аудиофайлы для каждой группы транскрипционных файлов. 
        Если все файлы готовы, вызывается функция для их объединения и отправки результата на API.
        """

        async with self.lock:
            if all_files_ready():
                await merge_transcription_files()
            await send_result_to_api()


def watch_folders():
    """
    Запускает наблюдение за папками с транскрипциями и входными аудиофайлами.

    Эта функция создает и запускает наблюдателя за папками `transcriptions` и `incoming_audio`, 
    отслеживая создание новых транскрипционных файлов. Если файл транскрипции создан, 
    запускается его обработка с использованием `TranscriptionFileHandler`.

    Асинхронно запускает событийный цикл и наблюдатель.
    """

    transcriptions_folder = Path("transcriptions")
    incoming_audio_folder = Path("incoming_audio")
    transcriptions_folder.mkdir(parents=True, exist_ok=True)
    incoming_audio_folder.mkdir(parents=True, exist_ok=True)

    loop = asyncio.get_event_loop()
    event_handler = TranscriptionFileHandler(loop)
    observer = Observer()

    observer.schedule(event_handler, str(transcriptions_folder), recursive=False)

    observer.start()
    print(f"Watching folders: {transcriptions_folder} and {incoming_audio_folder}")

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    watch_folders()

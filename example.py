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
    files = sorted(files, key=lambda f: f.stem)
    async with aiofiles.open(output_file, "w", encoding="utf-8") as outfile:
        for file in files:
            async with aiofiles.open(file, "r", encoding="utf-8") as infile:
                content = await infile.read()
                await outfile.write(content + "\n")
    print(f"Merged: {output_file}")


def all_files_ready():
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
    def __init__(self, loop):
        self.loop = loop
        self.last_call_time = 0
        self.debounce_interval = 3  # seconds
        self.lock = asyncio.Lock()

    def on_created(self, event):
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
        async with self.lock:
            if all_files_ready():
                await merge_transcription_files()
            await send_result_to_api()


def watch_folders():
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
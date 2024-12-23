import os
import time
from watchdog.observers import Observer
from file_watcher import AudioFileHandler

def start_server(watch_directory: str, output_directory: str):
    """
    Запускает сервер для наблюдения за директориями.
    """
    event_handler = AudioFileHandler(output_directory)
    observer = Observer()
    observer.schedule(event_handler, path=watch_directory, recursive=False)

    print(f"Сервер запущен. Наблюдение за директорией: {watch_directory}")
    observer.start()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    watch_directory = "./incoming_audio"
    output_directory = "./transcriptions"

    # Создаем директории, если они не существуют
    os.makedirs(watch_directory, exist_ok=True)
    os.makedirs(output_directory, exist_ok=True)

    # Запуск сервера
    start_server(watch_directory, output_directory)

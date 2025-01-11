import logging

import aiofiles
import uvicorn
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Request, Depends
from typing import Dict, List

from pydantic import BaseModel
from pydub import AudioSegment
from pydub.utils import mediainfo
from sqlalchemy.ext.asyncio import AsyncSession

from config import UPLOAD_FOLDER, INCOMING_AUDIO_DIR
from database import get_async_session
from utils import send_result_to_api

app = FastAPI()
audio_counter = 0

def create_unique_folder():
    """Создает уникальную папку для каждого запроса на основе времени"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    folder_path = UPLOAD_FOLDER / timestamp
    folder_path.mkdir(parents=True, exist_ok=True)
    return folder_path



def save_audio_segments(audio_file_path, segment_duration=30, save_folder=None):
    """
    Разделяет аудиофайл на сегменты указанной продолжительности и сохраняет их в указанной папке.

    Эта функция принимает путь к аудиофайлу, разделяет его на сегменты продолжительностью 
    по умолчанию 30 секунд (или заданное время), и сохраняет каждый сегмент как отдельный 
    файл в папке `save_folder`. Если папка не указана, сегменты сохраняются в директории 
    `INCOMING_AUDIO_DIR`. Каждому сегменту присваивается уникальное имя с использованием 
    счетчика и информации о типе записи (MIC или SPEAKER).

    Аргументы:
        audio_file_path (str): Путь к исходному аудиофайлу.
        segment_duration (int, optional): Длительность сегмента в секундах (по умолчанию 30).
        save_folder (str, optional): Папка для сохранения сегментов (по умолчанию None).

    Возвращает:
        list: Список путей к сохраненным сегментам.
    """
    global audio_counter
    try:
        audio = AudioSegment.from_wav(audio_file_path)
        audio_length = len(audio)
        segment_number = 0
        segment_paths = []

        file_name = Path(audio_file_path).stem
        mic_or_speaker = ""
        if "MIC" in file_name.upper():
            mic_or_speaker = "MIC"
        elif "SPEAKER" in file_name.upper():
            mic_or_speaker = "SPEAKER"

        while segment_number * segment_duration * 1000 < audio_length:
            segment_start = segment_number * segment_duration * 1000
            segment_end = min((segment_number + 1) * segment_duration * 1000, audio_length)

            segment = audio[segment_start:segment_end]

            segment_filename = f"audio_part_{str(audio_counter).zfill(3)}_{str(segment_number).zfill(3)}"
            if mic_or_speaker:
                segment_filename += f"_{mic_or_speaker}"
            segment_filename += ".wav"

            if save_folder:
                segment_path = Path(save_folder) / segment_filename

            segment_path = INCOMING_AUDIO_DIR / segment_filename

            segment.export(segment_path, format="wav")
            print(f"Saved segment {segment_filename} to {segment_path}")

            segment_paths.append(segment_path)
            segment_number += 1

        audio_counter += 1

        return segment_paths

    except Exception as e:
        logging.error(f"Error while processing audio file: {str(e)}")
        return []

class DataModel(BaseModel):
    operator: dict
    client: dict
    order_id: str
    status_1c: str
    status_ai: str
    call_id: str
    call_info: str
    datetime: str
    audio_path: str

@app.post("/test-api")
async def receive_data(data: DataModel):
    print(f"Received data: {data.dict()}")
    return {"status": "success", "received_data": data.dict()}




@app.post("/upload")
async def upload_file(
        files: List[UploadFile] = File(None),
        request: Request = None,
        session: AsyncSession = Depends(get_async_session),
):
    """
    Обрабатывает загружаемые файлы (JSON и аудио), сохраняет их в уникальной папке и 
    выполняет сегментацию аудиофайлов.

    Эта функция принимает файлы, загруженные пользователем (JSON и/или аудио), сохраняет их 
    в папку с уникальным именем, созданным с использованием текущего времени. Затем она 
    проверяет длину аудиофайла и, если он слишком короткий, сохраняет его без сегментации. 
    Для длинных файлов выполняется сегментация на части заданной продолжительности (по умолчанию 30 секунд). 
    Все файлы обрабатываются асинхронно.

    Аргументы:
        files (List[UploadFile]): Список файлов для обработки (может содержать как JSON, так и аудио).
        request (Request): Объект запроса FastAPI.
        session (AsyncSession): Асинхронная сессия для работы с базой данных.

    Возвращает:
        dict: Статус обработки файлов (сообщение об успехе или ошибке).
    """
    
    try:
        save_folder = create_unique_folder()
        logging.info(f'Created folder: {save_folder}')

        form_data = {}
        audio_file = None
        json_file = None
        audio_counter = 0
        print("before", audio_counter)
        if len(files) == 1 and files[0].filename.endswith(".json"):
            json_file = files[0]
            json_data_path = save_folder / json_file.filename
            async with aiofiles.open(json_data_path, "wb") as json_file_path:
                await json_file_path.write(await json_file.read())
            logging.info(f'Saved JSON data: {json_data_path}')

            return {"message": "JSON file processed and saved successfully."}

        segment_paths = []

        for file in files:
            logging.info(f'Processing file: {file.filename}')

            if file.filename.endswith(".json"):
                form_data_path = save_folder / file.filename
                async with aiofiles.open(form_data_path, "wb") as f:
                    await f.write(await file.read())
                logging.info(f'Saved form data: {form_data_path}')

            elif file.filename.endswith(".wav"):
                logging.info(f'Processing audio file: {file.filename}')
                audio_file = file
                audio_file_path_1 = save_folder / file.filename

                async with aiofiles.open(audio_file_path_1, "wb") as f_audio_1:
                    await f_audio_1.write(await file.read())
                logging.info(f'Saved audio file in main folder: {audio_file_path_1}')

                logging.info(f"Checking audio length for: {audio_file.filename}")
                audio = AudioSegment.from_file(audio_file_path_1)

                audio_length = len(audio) / 1000
                print(audio_length)
                logging.info(f"Audio length: {audio_length} seconds.")
                if audio_length < 30:
                    segment_filename = audio_file.filename
                    segment_path = INCOMING_AUDIO_DIR / segment_filename
                    async with aiofiles.open(segment_path, "wb") as f_audio:
                        await f_audio.write(await audio_file.read())
                    logging.info("Returning response for short audio file.")
                    return {"message": "Audio file saved successfully in incoming audio folder."}

                logging.info(f"Segmenting audio file: {audio_file_path_1}")
                segment_paths = save_audio_segments(audio_file_path_1,
                                                    save_folder=save_folder)
                logging.info(f"Saved {len(segment_paths)} audio segments.")
                audio_counter += 1
                print("after>", audio_counter)
        logging.info("Completed processing all files.")
        return {"message": "All files processed successfully."}

    except Exception as e:
        logging.error(f"Error while uploading: {str(e)}")
        return {"error": str(e)}



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run("main:app", host="0.0.0.0", port=8082, reload=True)

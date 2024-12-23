import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
UPLOAD_FOLDER = Path('uploads')
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
INCOMING_AUDIO_DIR = Path('./incoming_audio')

DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

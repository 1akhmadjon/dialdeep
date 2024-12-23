import os
import numpy as np
from pydub import AudioSegment


def preprocess_audio(file_path: str) -> np.ndarray:
    """
    Предобрабатывает аудиофайл:
    - Конвертация в моно, установка частоты дискретизации на 16 кГц.
    - Удаление шума и нормализация громкости.
    - Преобразование в numpy массив.

    Параметры:
    file_path (str): Путь к аудиофайлу.

    Возвращает:
    np.ndarray: Предобработанные аудиоданные.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Аудиофайл {file_path} не найден.")

    # Загрузка аудио
    audio = AudioSegment.from_file(file_path)

    # Преобразование в моно, нормализация громкости
    audio = audio.set_channels(2).set_frame_rate(32000).normalize()

    # Конвертация в numpy массив
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)

    # Нормализация данных (диапазон от -1 до 1)
    samples = samples / np.max(np.abs(samples))

    return samples

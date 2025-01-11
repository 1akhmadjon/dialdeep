import json
import logging
import os
from pathlib import Path
from typing import List
from datetime import datetime
from collections import defaultdict
import aiofiles
import aiohttp
import requests
from pydub import AudioSegment
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from config import UPLOAD_FOLDER
from database import get_async_session
from models.models import client_table, call_info_table, operator_table

def get_files():
    """
    Извлекает файлы form_data и JSON из указанной папки для загрузки.

    Эта функция ищет директории, начинающиеся с '2024', в директории 
    `UPLOAD_FOLDER`, затем проверяет наличие файлов `form_data.json` и 
    `json_data.json` в этих папках. Функция возвращает пути найденных файлов 
    в словаре с ключами 'form_data_files' и 'json_files'.

    Возвращает:
        dict: Словарь, содержащий пути к файлам form_data.json и json_data.json.
    """
    form_data_files = []
    json_files = []

    for folder in os.listdir(UPLOAD_FOLDER):
        folder_path = UPLOAD_FOLDER / folder

        if folder_path.is_dir() and folder.startswith("2024"):
            form_data_path = folder_path / "form_data.json"
            json_data_path = folder_path / "json_data.json"

            if form_data_path.exists():
                form_data_files.append(form_data_path)

            if json_data_path.exists():
                json_files.append(json_data_path)

    return {'form_data_files': form_data_files, 'json_files': json_files}


async def send_result_to_api():
    """
    Обрабатывает файлы form_data и JSON, форматирует данные и отправляет их 
    во внешний API, а также сохраняет в базу данных.

    Эта функция фильтрует файлы form_data по их временной метке (обрабатываются 
    только файлы за последние 3 минуты). Затем она пытается сопоставить данные 
    form_data с соответствующими данными JSON по имени пользователя. Если совпадение 
    найдено, данные форматируются и отправляются на указанный API-эндпоинт, 
    а также сохраняются в базе данных. Обработанные файлы отслеживаются, чтобы избежать 
    повторной обработки.

    Возвращает:
        list: Пустой список (для будущих расширений).
    """
    files = get_files()
    form_data_files = files.get('form_data_files', [])
    json_files = files.get('json_files', [])

    if not form_data_files or not json_files:
        print("form_data_files yoki json_files fayllari topilmadi")
        return []

    processed_files_path = 'processed_files.txt'
    processed_files = set()
    if os.path.exists(processed_files_path):
        with open(processed_files_path, 'r', encoding='utf-8') as f:
            processed_files = set(f.read().splitlines())

    current_time = datetime.now()

    valid_form_data_files = []
    for form_data_path in form_data_files:
        try:
            dir_name = os.path.basename(os.path.dirname(form_data_path))
            timestamp_str = dir_name.split('_')[1][:4]
            timestamp = datetime.strptime(timestamp_str, '%H%M')

            current_total_minutes = current_time.hour * 60 + current_time.minute
            timestamp_total_minutes = timestamp.hour * 60 + timestamp.minute
            time_difference_minutes = current_total_minutes - timestamp_total_minutes

            if 0 <= time_difference_minutes <= 3:
                valid_form_data_files.append(form_data_path)
        except Exception as e:
            print(f"form_data faylidan timestampni olishda xato: {str(e)}")

    form_data_list = []
    for form_data_path in valid_form_data_files:
        try:
            with open(form_data_path, "r", encoding="utf-8") as f:
                form_data = json.load(f)
                form_data_dir = os.path.dirname(form_data_path)

                form_data['audio_path'] = None
                for file in os.listdir(form_data_dir):
                    if file.endswith('.wav'):
                        form_data['audio_path'] = os.path.join(form_data_dir, file)
                        break

                form_data_list.append(form_data)
        except Exception as e:
            print(f"form_data faylini o'qishda xato: {str(e)}")

    for json_data_path in json_files:
        try:
            with open(json_data_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            json_data_user = None
            phone_number = None
            order_id = None
            status_1c = None
            timestamp = None
            client_id = None
            operator_id = None

            for key, value in json_data.items():
                if isinstance(value, dict) and 'USER_NAME' in value:
                    json_data_user = value.get('USER_NAME')
                    phone_number = value.get('1C_OUTPUT', {}).get("field_101")
                    order_id = value.get('1C_OUTPUT', {}).get("field_2")
                    status_1c = value.get('1C_OUTPUT', {}).get("field_36")
                    timestamp = value.get('1C_OUTPUT', {}).get("field_3")
                    client_id = value.get('1C_OUTPUT', {}).get("field_101")
                    operator_id = value.get('1C_OUTPUT', {}).get("field_2")
                    break

            if not json_data_user:
                print(f"USER_NAME json faylida topilmadi: {json_data_path}")
                continue

            matched_form_data = next(
                (form_data for form_data in form_data_list if form_data.get('salesman_username') == json_data_user),
                None
            )

            if matched_form_data:
                call_info = matched_form_data.get("call_info", "")
                call_id = matched_form_data.get("call_id", "")
                audio_path = matched_form_data.get("audio_path", "")
                formatted_datetime = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')

                form_data_dir_name = os.path.basename(os.path.dirname(json_data_path))
                audio_dir_name = os.path.basename(os.path.dirname(audio_path))


                if any(line == form_data_dir_name or line == audio_dir_name for line in processed_files):
                    continue

                record = {
                    "operator": {
                        "id": json_data_user,
                        "name": json_data_user
                    },
                    "client": {
                        "id": client_id,
                        "phone": phone_number
                    },
                    "order_id": order_id,
                    "status_1c": status_1c,
                    "status_ai": "approved",
                    "call_id": call_id,
                    "call_info": call_info,
                    "datetime": formatted_datetime,
                    "audio_path": audio_path
                }

                await save_data_to_db([record])


                api_url = "http://127.0.0.1:8000/test-api"
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.post(api_url, json=record) as response:
                            if response.status == 200:
                                print(f"Ma'lumot muvaffaqiyatli yuborildi: {record}")

                                # Mark directories as processed
                                with open(processed_files_path, 'a', encoding='utf-8') as f:
                                    f.write(f"{form_data_dir_name}\n")
                                    f.write(f"{audio_dir_name}\n")
                            else:
                                print(f"Ma'lumot yuborishda xato: {record}, Status: {response.status}")
                    except Exception as e:
                        print(f"API ga yuborishda xato: {str(e)}")

        except Exception as e:
            print(f"json faylini ishlashda xato: {str(e)}")

    return []






async def save_data_to_db(data):
    """
    Сохраняет обработанные данные в базе данных, обеспечивая, что операторы, клиенты 
    и заказы правильно вставляются без дублирования.

    Эта функция сначала проверяет, существуют ли оператор и клиент в базе данных. 
    Если они не существуют, то вставляются. Также проверяется, существует ли заказ с 
    данным идентификатором. Если заказа нет, он вставляется в таблицу `call_info_table`. 
    Функция использует SQLAlchemy для выполнения операций с базой данных асинхронно.

    Аргументы:
        data (list): Список записей для сохранения в базе данных.
    """
    async for session in get_async_session():
        try:
            for record in data:

                operator_stmt = select(operator_table).where(operator_table.c.name == record["operator"]["name"])
                result = await session.execute(operator_stmt)
                existing_operator = result.fetchall()

                if existing_operator:
                    operator_id = existing_operator[0].id
                else:
                    operator_name = record["operator"]["name"]
                    operator_stmt = insert(operator_table).values(
                        name=operator_name
                    ).returning(operator_table.c.id)
                    res = await session.execute(operator_stmt)
                    operator_id = res.scalar()


                client_stmt = select(client_table).where(client_table.c.phone == record["client"]["phone"])
                result = await session.execute(client_stmt)
                existing_client = result.fetchall()


                if existing_client:
                    client_id = existing_client[0].id
                else:
                    client_name = record["client"].get("name", "")
                    client_phone = record["client"]["phone"]
                    client_stmt = insert(client_table).values(
                        name=client_name,
                        phone=client_phone
                    )
                    await session.execute(client_stmt)
                    client_id = await session.scalar(select(client_table.c.id).where(client_table.c.phone == client_phone))

                call_info_check_stmt = select(call_info_table).where(call_info_table.c.order_id == record["order_id"])
                result = await session.execute(call_info_check_stmt)
                existing_order = result.fetchone()

                if existing_order:
                    print(f"Order ID {record['order_id']} allaqachon mavjud, o'tkazib yuborilmoqda.")
                    continue
                else:
                    call_info_stmt = insert(call_info_table).values(
                        operator_id=operator_id,
                        client_id=client_id,
                        operator_txt=None,
                        client_txt=None,
                        dialog_txt=None,
                        status_ai=record["status_ai"],
                        status_1c=record["status_1c"],
                        datetime=record["datetime"],
                        order_id=record["order_id"],
                        call_id=record["call_id"],
                        call_info=record["call_info"],
                        audio_path=record["audio_path"]
                    )
                    await session.execute(call_info_stmt)
                    print("Ma'lumot bazaga muvaffaqiyatli saqlandi")

            await session.commit()

        except IntegrityError as e:
            await session.rollback()
            print(f"Ma'lumotni saqlashda xato yuz berdi (IntegrityError): {str(e)}")
        except Exception as e:
            await session.rollback()
            print(f"Ma'lumotni saqlashda xato yuz berdi: {str(e)}")

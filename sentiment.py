import re
import pandas as pd
from freeGPTFix import Client
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os

model_name = "blackhole33/finetuning-sentiment-model-uzb"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model_X = AutoModelForSequenceClassification.from_pretrained(model_name)


def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text


def check_greeting(text):
    greetings = ["salom", "alayk", "alakum", "assalomu alaykum"]
    cleaned_text = text.lower().strip()
    sentences = cleaned_text.split('.')
    for i, sentence in enumerate(sentences[:5]):
        for greeting in greetings:
            if greeting in sentence:
                return 1
    if any(greeting in cleaned_text.split()[-5:] for greeting in greetings):
        return 0
    return 0


def check_name_asked(text):
    keywords = ["ismingiz nima", "ismingizni ayta olasizmi", "ismingizni bilsam bo'ladimi", "ismiz" "ismingiz"]
    for keyword in keywords:
        if keyword in text:
            return 1
    return 0


def check_company_discussed(text):
    keywords = ["euphoria", "eyforiya"]
    for keyword in keywords:
        if keyword in text:
            return 1
    return 0


def check_medicine_info(text):
    keywords = ["sizning ichki organizmlaringizni yuvib", "prostatadagi infeksiya", "kasallik",
                "shamollash", "yallig'lanish", "siydik yo'lidagi qum", "tosh", "tuzlarni yuvib beradi",
                "bir hafta ichida sizni hozirgiga nisbatan ko'proq peshobga chiqishga majbur qiladi",
                "sababi sizni ichki organizimlaringizni tozalash jarayoni ketayotgani hisobiga",
                "75% gacha sizning testesteroningizni joyiga qaytarib beradi",
                "aloqa vaqtini 20 25 daqiqagacha cho'zib beradi",
                "15 daqiqadan 20 daqiqacha uzaytirib beradi", "qon tomirlarini", "qon aylanishlarini yaxshilab beradi",
                "ko'rish xususiyatlarini yaxshilab beradi",
                "uzoni ko'rishdagi muammoni yaxshilaydi", "yaqinni ko'rishdagi muammoni",
                "yoshlanish achishish toliqish kabi muammolarni bartaraf qilib beradi",
                "3 kundan 5 kun ichida effekt ko'rasiz"]
    for keyword in keywords:
        if keyword in text:
            return 1
    return 0


def check_name_medicine(text):
    keywords = ["urion", "all day", "dibetikfortе", "fatality", "slimfit", "grow x", "gemoplus", "parazitoff",
                "do active", "sustafleks", "visucaps", "gipertofort", "menspower", "mens power"]
    for keyword in keywords:
        if keyword in text:
            return 1
    return 0


def check_seller_info(text):
    keywords = ["mening ismim", "euphoria kompaniyadan mutaxasisman", "mutaxasis",
                "bosh mutaxasis bo'laman", "urolig vrach", "sizga biriktirilgan mutaxasis bo'laman", "ismim",
                "bosh mutaxasis"]
    for keyword in keywords:
        if keyword in text:
            return 1
    return 0

def check_illness_symptoms(text):
    keywords = ["sizni nima bezovta qilayobdi", "qayeringiz og'riyobdi",
                "qanday bezovtaliklar bor", "sizga qanday yordam bera olaman", "nimada muammolar bor"]
    for keyword in keywords:
        if keyword in text:
            return 1
    return 0


def predict_sentiment(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    outputs = model_X(**inputs)
    probabilities = torch.softmax(outputs.logits, dim=-1)
    negative_percentage = probabilities[0][0].item() * 100
    positive_percentage = probabilities[0][1].item() * 100
    return f"Positive: {positive_percentage:.2f}%, Negative: {negative_percentage:.2f}%"


def analyze_conversation(conversation):
    cleaned_text = clean_text(conversation)

    sentiment_result = predict_sentiment(cleaned_text)
    greeting_check = check_greeting(cleaned_text)
    name_check = check_name_asked(cleaned_text)
    company_check = check_company_discussed(cleaned_text)
    medicine_check = check_medicine_info(cleaned_text)
    seller_check = check_seller_info(cleaned_text)
    illness_check = check_illness_symptoms(cleaned_text)
    name_medicine_check = check_name_medicine(cleaned_text)

    inputs = tokenizer(cleaned_text, return_tensors="pt", truncation=True, padding=True)
    outputs = model_X(**inputs)
    predictions = outputs.logits.argmax(dim=-1).item()

    sale_result = 1 if predictions == 1 else 0

    return {
        'sentiment': sentiment_result,
        'Salomlashish': greeting_check,
        'Ism_so\'rash': name_check,
        'Sotuvchi_haqida': seller_check,
        'Kompaniya': company_check,
        'Dori_haqida': medicine_check,
        'Kasalligini_so\'rash': illness_check,
        'Dorining_nomi': name_medicine_check,
        'Buyurtma': sale_result
    }


def xaridni_aniqlash(request_text: str) -> str:
    prompt = f"Bu suhbatda mijoz dorini sotib olganmi yoki olmaganmi? Menga bitta gap bilan javob ber, Buyurtma tasdiqlandi yoki Buyurtma tasdiqlanmadi Suhbat: {request_text}"
    try:
        resp = Client.create_completion("gpt4", prompt)
        javob = resp.strip().lower()

        if "sotib olgan" in javob or "Buyurtma tasdiqlandi" in javob or "tasdiqlandi" in javob:
            return "Buyurtma tasdiqlandi"
        else:
            return "Buyurtma tasdiqlanmadi"
    except Exception as e:
        print(f"Error while generating analysis response: {e}")
        return "Xatolik yuz berdi."

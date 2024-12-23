from typing import Dict
from sentiment import analyze_conversation, xaridni_aniqlash



def analyze_text(text: str) -> Dict[str, int]:
    """
    Выполняет базовый анализ текста:
    - Подсчет слов.
    - Подсчет уникальных слов.
    - Средняя длина слова.

    Параметры:
    text (str): Текст для анализа.

    Возвращает:
    Dict[str, int]: Результаты анализа текста.
    """
    words = text
    words_split = text.split()
    word_count = len(words_split)
    unique_words = len(set(words_split))
    avg_word_length = sum(len(word) for word in words_split) / word_count if word_count else 0
    analysis_result = analyze_conversation(words)
    sale_result = xaridni_aniqlash(words)

    return {
        "word_count": word_count,
        "unique_words": unique_words,
        "avg_word_length": avg_word_length,
        "analysis_result": analysis_result,
        "sale_result": sale_result
    }

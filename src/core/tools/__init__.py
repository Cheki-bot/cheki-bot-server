import re
import string
from datetime import datetime

import pytz


def sanitize_text_input(text: str) -> str:
    text = text.lower()
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    text = re.sub(r"@\w+|#\w+", "", text)
    text = re.sub(r"[^\w\s.,;]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([.,;])", r"\1", text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    return text


def get_current_datetime():
    return datetime.now()


def get_bo_current_datetime_str():
    bo_tz = pytz.timezone("America/La_Paz")
    dt_bo = bo_tz.localize(get_current_datetime())
    return dt_bo.strftime("%d/%m/%Y %H:%M:%S")

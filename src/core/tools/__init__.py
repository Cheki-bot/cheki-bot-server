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


def bo_str_date_to_datetime(str_date: str) -> datetime:
    months = [
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    ]
    str_date = str_date.lower()

    pattern = r"(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})"
    match = re.search(pattern, str_date)
    if not match:
        raise ValueError(f"Invalid date format: {str_date}")

    day = int(match.group(1))
    month_str = match.group(2)
    year = int(match.group(3))
    month = months.index(month_str) + 1
    return datetime(year, month, day)

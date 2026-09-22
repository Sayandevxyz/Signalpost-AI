import re


def normalize_registration_number(value: str) -> str:
    value = re.sub(r"\s+", "", value)
    if not re.fullmatch(r"\d{9}", value):
        raise ValueError("Norwegian company number must contain exactly 9 digits")
    return value

def normalize_amount(value: str) -> float:
    return float(value.replace(" ", "").replace(".", "").replace(",", "."))

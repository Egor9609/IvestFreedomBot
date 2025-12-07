# bot/utils/helpers.py

def to_float(value) -> float:
    if value is None:
        return 0.0
    return float(value)
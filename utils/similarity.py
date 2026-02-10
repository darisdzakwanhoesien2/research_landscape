from rapidfuzz import fuzz

def similarity(a: str, b: str):
    return fuzz.token_set_ratio(a, b) / 100.0

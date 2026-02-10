import re

def normalize_text(text: str):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# import re

# def normalize_text(text: str):
#     if not text:
#         return ""
#     text = text.lower()
#     text = re.sub(r"[^a-z0-9 ]", " ", text)
#     text = re.sub(r"\s+", " ", text)
#     return text.strip()


# import re

# def normalize_text(text: str):
#     if not text:
#         return ""
#     text = text.lower()
#     text = re.sub(r"[^a-z0-9 ]", " ", text)
#     text = re.sub(r"\s+", " ", text)
#     return text.strip()
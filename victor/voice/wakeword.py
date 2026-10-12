import re
import unicodedata


def extract_command(text: str, wake_word: str, required: bool = True):
    def normalize(value):
        return "".join(c for c in unicodedata.normalize("NFD", value) if unicodedata.category(c) != "Mn")
    match = re.search(r"(?<!\w)" + re.escape(normalize(wake_word.strip())) + r"(?!\w)[\s,:;.!¿?¡-]*", normalize(text), re.IGNORECASE)
    if match:
        return text[match.end():].strip()
    return "" if required else text.strip()

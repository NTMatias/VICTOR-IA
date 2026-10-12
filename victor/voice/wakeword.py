import re
import unicodedata


def extract_command(text: str, wake_word: str, required: bool = True):
    def normalize(value):
        return "".join(c for c in unicodedata.normalize("NFD", value) if unicodedata.category(c) != "Mn")
    match = re.search(r"(?<!\w)" + re.escape(normalize(wake_word.strip())) + r"(?!\w)[\s,:;.!¿?¡-]*", normalize(text), re.IGNORECASE)
    if match:
        return text[match.end():].strip()
    # Variantes fonéticas delimitadas, solo al comienzo. Nunca un prefijo
    # de otra palabra (p. ej. «victoria»), ni una autorización afirmativa.
    if normalize(wake_word.strip()).casefold() == 'victor':
        variant = re.match(r'^\s*(?:bictor|viktor|vitor|vicktor)(?!\w)[\s,:;.!¿?¡-]*', normalize(text), re.IGNORECASE)
        if variant:
            return text[variant.end():].strip()
    return "" if required else text.strip()

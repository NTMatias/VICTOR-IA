"""Vocabulario personal, correcciones explícitas y texto legible por los motores TTS."""
import html
import re
import unicodedata
from victor.errors import VictorError


def folded(text):
    return " ".join("".join(c for c in unicodedata.normalize("NFKD", text.casefold())
                    if not unicodedata.combining(c)).split()).strip(" .,!¡?¿")


def correction_pairs(value):
    result = {}
    for line in value.splitlines():
        if not line.strip():
            continue
        parts = line.split("=>")
        if len(parts) != 2 or any(not p.strip() or len(p.strip()) > 200 for p in parts):
            raise VictorError("Correcciones de voz: escribe una por línea, como la mina de Chris R => GAMINA de Kris R.")
        source, target = parts
        key = folded(source)
        if key in result:
            raise VictorError("Hay una corrección de voz repetida.")
        result[key] = target.strip()
    return result


def correct_music_command(text, corrections):
    # Solo coincidencias completas del título/artista en una orden de reproducción.
    # No altera dictado libre, comandos de archivos ni frases de confirmación.
    match = re.fullmatch(r"((?:reproduce|reproducir|pon|poner|toca|tocar)\s+(?:(?:la canción|el tema)\s+)?)(.+?)"
                         r"(\s+(?:(?:en|n|de|del)\s+)?(?:spotify|sporify|espotify))?([.!?]*)",
                         text.strip(), flags=re.I)
    if not match:
        return text
    target = correction_pairs(corrections).get(folded(match[2]))
    service = match[3] or ""
    # Whisper puede representar la preposición oral «en» como la letra «N».
    service = re.sub(r"^\s+n\s+", " en ", service, flags=re.I)
    if target or service != (match[3] or ""):
        return match[1] + (target or match[2]) + service + match[4]
    return text


def recognition_vocabulary(cfg):
    names = re.split(r"[,\n]+", cfg.get("voice_vocabulary", ""))
    names += [cfg.get("wake_word", "VICTOR")]
    names += list(cfg.get("applications", {}))
    names += list(correction_pairs(cfg.get("voice_corrections", "")).values())
    return ", ".join(dict.fromkeys(n.strip() for n in names if n.strip()))[:1400]


def speech_text(text):
    if not text:
        return ""
    text = unicodedata.normalize('NFC', html.unescape(str(text)))
    text = re.sub(r"```.*?```", " He incluido un bloque de código en el chat. ", text, flags=re.S)
    lines=text.splitlines();spoken=[];index=0
    def cells(line):return [cell.strip() for cell in re.split(r'(?<!\\)\|',line.strip().strip('|'))]
    while index<len(lines):
        if index+1<len(lines) and '|' in lines[index] and '|' in lines[index+1] and all(re.fullmatch(r':?-{3,}:?',cell) for cell in cells(lines[index+1])):
            headers=cells(lines[index]);index+=2
            while index<len(lines) and '|' in lines[index]:
                row=cells(lines[index]);spoken.append('; '.join(header+': '+value for header,value in zip(headers,row))+'.');index+=1
        else:
            if not re.fullmatch(r'\s*[-*_]{3,}\s*',lines[index]):spoken.append(lines[index])
            index+=1
    text='\n'.join(spoken)
    text = re.sub(r"!?\[([^\]]+)\]\([^\n)]+\)", r"\1", text)
    text = re.sub(r"<\/?[a-zA-Z][^>]*>", "", text)
    text = re.sub(r"https?://\S+", "enlace", text)
    text = re.sub(r"(?m)^\s*(?:#{1,6}\s+|>\s+|[-*•]\s+)", "", text)
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text, flags=re.S)
    text = re.sub(r"(?<!\w)([*_])([^\n]+?)\1(?!\w)", r"\2", text)
    text = text.replace("`", "")
    # Paréntesis/corchetes son pausas: el contenido sigue leyéndose.
    text = re.sub(r"[()\[\]{}]", ", ", text)
    text = re.sub(r'["“”«»]', "", text)
    text = "".join(c for c in text if unicodedata.category(c) != "So" and c not in "\ufe0f\u200d")
    text = re.sub(r"(\d)\s*%", r"\1 por ciento", text)
    text = text.replace("&", " y ").replace("|", ", ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(?<!\d),(?:\s*,)*\s*|,\s*(?!\d)", ", ", text)
    text = re.sub(r",\s*([.!?:;])", r"\1", text)
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    return text.strip(" ,")

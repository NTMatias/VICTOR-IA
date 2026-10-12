"""Intenciones musicales explícitas, compartidas por voz, chat y herramienta."""
import re


def artist_request(query):
    match=re.fullmatch(r"(?:(?:cualquier|alguna|una)\s+canci[oó]n|(?:cualquier|alg[uú]n|un)\s+tema|canciones|temas|m[uú]sica|algo|una)\s+(?:de\s+|del\s+(?:artista|cantante|grupo|banda)\s+)(.+)",query.strip(),re.I)
    return match[1].strip() if match else None

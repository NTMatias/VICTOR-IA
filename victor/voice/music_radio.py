"""Una sola elección por canción: 20 % por frase y 60 % sin coletilla."""
import random


def radio_phrase():
    value=random.randrange(100)
    if value < 20:return 'Lo escuchas aquí en VICTOR.IA.'
    if value < 40:return 'Escuchándose en Spotify desde VICTOR.IA.'
    return ''

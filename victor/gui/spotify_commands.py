"""Route spoken Spotify requests to real tools, without an LLM acknowledgement."""
import re


def spotify_command(text, wake_word='victor', state=None):
    text=text.strip().strip(' .,!¡?¿')
    text=re.sub(r'^(?:por favor[, ]+)', '',text,flags=re.I)
    names={'victor','victoria',wake_word.strip()}
    prefix='|'.join(re.escape(name) for name in names if name)
    text=re.sub(r'^(?:'+prefix+r')[, :]+','',text,flags=re.I)
    text=re.sub(r'[, ]+por favor$','',text,flags=re.I)
    service=re.search(r'\s+(?:(?:en|de|del)\s+)?(?:spotify|sporify|espotify)$',text,re.I)
    if service:
        text=text[:service.start()].strip()
    active_music = bool(state and state.get('id'))
    # Controles breves durante una conversación musical; no dependen de IA.
    if service or active_music:
        volume = re.fullmatch(r'(?:pon|poner|ajusta|ajustar|cambia|cambiar|baja|sube)?\s*(?:el\s+)?volumen\s+(?:(?:al|a|en)\s+)?(\d{1,3})\s*(?:%|por ciento)?', text, re.I)
        if volume:
            level = int(volume[1])
            if 0 <= level <= 100: return 'spotify_volume', {'level': level}
            return None
        relative = re.fullmatch(r'(sube|baja)(?:\s+(?:el\s+)?volumen)', text, re.I)
        if relative and state and isinstance(state.get('volume'), (int, float)):
            level = round(state['volume']) + (10 if relative[1].lower() == 'sube' else -10)
            return 'spotify_volume', {'level': max(0, min(100, level))}
        if re.fullmatch(r'(?:cambia|cambiar|salta|saltar)(?:\s+(?:la|de))?\s+canci[oó]n', text, re.I):
            return 'spotify_next', {}
        if re.fullmatch(r'(?:pon(?:le)?|poner(?:le)?|dale|darle)\s+pausa(?:\s+a)?(?:\s+(?:la\s+)?(?:canci[oó]n|m[uú]sica|reproducci[oó]n))?',text,re.I):
            return 'spotify_pause', {}
    play=re.fullmatch(r'(?:reproduce|reproducir|pon|poner|toca|tocar)\s+(.+)',text,re.I)
    if play:
        from victor.integrations.music_intent import artist_request
        explicit_music=bool(re.match(r'^(?:la canci[oó]n|el tema|el sencillo)\s+',play[1],re.I))
        query=re.sub(r'^(?:la canci[oó]n|el tema|el sencillo)\s+','',play[1],flags=re.I).strip()
        if not service and not re.match(r'^(?:reproduce|reproducir)\s+',text,re.I) and not explicit_music and not artist_request(query):return None
        if re.match(r'^(?:(?:la|mi|una|el|un)\s+)?(?:playlist|lista|[aá]lbum|podcast)\b',query,re.I):return None
        if not service and re.search(r'\b(?:video|v[ií]deo|archivo|grabaci[oó]n|youtube|mensaje)\b',query,re.I):return None
        if query:return 'spotify_play',{'query':query}
    if not service and not active_music:return None
    for pattern,name in [(r'(?:pausa|pausar|p[aá]usala)(?:\s+(?:la\s+)?(?:m[uú]sica|canci[oó]n|reproducci[oó]n))?','spotify_pause'),
                         (r'(?:contin[uú]a|continuar|reanuda|reanudar)(?:\s+(?:la\s+)?(?:m[uú]sica|canci[oó]n|reproducci[oó]n))?','spotify_resume'),
                         (r'(?:siguiente|pasa a la siguiente)(?: canci[oó]n)?','spotify_next'),
                         (r'(?:anterior|canci[oó]n anterior)','spotify_previous')]:
        if re.fullmatch(pattern,text,re.I):return name,{}
    return None


def unverified_spotify_answer(text):
    """The model cannot fabricate a tool wrapper and claim playback succeeded."""
    raw=str(text).strip()
    return raw.startswith('[Resultado de herramienta spotify_') or bool(
        re.match(r'^(?:```json\s*)?\{',raw) and 'orden_enviada' in raw and 'aceptada_por_api' in raw)

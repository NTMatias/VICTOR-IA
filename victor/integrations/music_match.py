"""Ordena coincidencias musicales sin confundir un título con otro hit relacionado."""
import re
import unicodedata
from difflib import SequenceMatcher


def normalized(text):
    text=''.join(c for c in unicodedata.normalize('NFKD',text).casefold() if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[^\W_]+',text))


def compact(text):
    return normalized(text).replace(' ','')


def title_variants(text):
    """Solo quitar créditos de colaboración; remix/live son versiones distintas."""
    credit = r'(?:feat\.?|ft\.?|featuring)\s+.+?'
    base = re.sub(r'\s*[\(\[]\s*'+credit+r'\s*[\)\]]\s*$', '', text, flags=re.I)
    base = re.sub(r'\s+(?:[-–—]\s*)?'+credit+r'\s*$', '', base, flags=re.I)
    return (text, base) if base.strip() and base != text else (text,)


def split_query(query):
    # El último «de» permite títulos como «Después de la Playa de Bad Bunny».
    parts = re.split(r'\s+de\s+', query.strip(), flags=re.I)
    return (' de '.join(parts[:-1]), parts[-1]) if len(parts)>1 else (query.strip(), '')


def similarity(first,second,artist=False):
    first,second=compact(first),compact(second)
    if not first or not second:return 0.
    if artist:
        # Grafías frecuentes del mismo sonido, aplicadas solo a artistas.
        def sound(value):return value.replace('chris','kris').replace('chr','kr').replace('ph','f')
        first,second=sound(first),sound(second)
    return SequenceMatcher(None,first,second,autojunk=False).ratio()


def exact_match(query,row):
    requested=compact(query);title=compact(row.get('name',''))
    if requested==title:return True  # Un título también puede contener «de».
    requested_title,artist=split_query(query)
    titles={compact(value) for value in title_variants(row.get('name',''))}
    if artist:
        return compact(requested_title) in titles and any(compact(artist)==compact(a.get('name','')) for a in row.get('artists',[]))
    return requested in titles or any(requested in (title+compact(a.get('name','')),title+'de'+compact(a.get('name','')))
                                     for a in row.get('artists',[]))


def nearest_match(query,rows):
    title,artist=split_query(query)
    scored=[]
    for row in rows:
        title_score=max(similarity(title,value) for value in title_variants(row.get('name','')))
        artist_score=max((similarity(artist,a.get('name',''),artist=True) for a in row.get('artists',[])),default=0.) if artist else 1.
        # Tolerar errores breves sin seleccionar una canción ajena solo por artista.
        if title_score < .70 or (artist and artist_score < .64):continue
        score=title_score*.72+artist_score*.28 if artist else title_score
        if score >= .78:
            scored.append((score,title_score,row.get('popularity',0) or 0,row))
    if not scored:return None
    best=max(scored,key=lambda item:item[:3])
    return best[3],round(best[0],3)

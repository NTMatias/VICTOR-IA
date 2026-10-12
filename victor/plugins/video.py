"""Acción acotada solicitada por IA: primer resultado público de YouTube."""
import json
import re
from victor.errors import VictorError
from victor.security import Risk
from victor.tools.registry import Tool


def first_video(document):
    match=re.search(r'(?:var\s+)?ytInitialData\s*=\s*',document)
    if not match:raise VictorError('YouTube no devolvió resultados legibles. Abre la búsqueda en el navegador.')
    try:data,_=json.JSONDecoder().raw_decode(document[match.end():])
    except ValueError:raise VictorError('No pude interpretar los resultados de YouTube.') from None
    pending=[data]
    while pending:
        item=pending.pop()
        if isinstance(item,dict):
            video=item.get('videoRenderer',{})
            identifier=video.get('videoId','')
            if re.fullmatch(r'[A-Za-z0-9_-]{11}',identifier):
                title=''.join(r.get('text','') for r in video.get('title',{}).get('runs',[]))
                return identifier,title
            # Evita resultados publicitarios y conserva el orden de resultados.
            pending.extend(reversed([v for k,v in item.items() if 'ad' not in k.lower()]))
        elif isinstance(item,list):pending.extend(reversed(item))
    raise VictorError('No encontré un video reproducible en los resultados públicos.')


def register_video(core):
    def play(query):
        import requests
        try:
            with requests.get('https://www.youtube.com/results',params={'search_query':query},timeout=(5,12),stream=True) as response:
                response.raise_for_status();data=bytearray()
                for block in response.iter_content(32768):
                    from victor.errors import check_cancel
                    check_cancel(core.cancel)
                    data.extend(block)
                    if len(data)>4_000_000:raise VictorError('La respuesta de YouTube excede el tamaño permitido.')
            identifier,title=first_video(data.decode('utf-8',errors='replace'))
            core.apps.open_url('https://www.youtube.com/watch?v='+identifier+'&autoplay=1')
            return {'video':title,'solicitud_apertura':'Primer resultado de YouTube',
                    'aviso':'Se pidió reproducción automática al navegador; anuncios, consentimiento y políticas del navegador pueden impedirla. No puedo confirmar que esté sonando.'}
        except VictorError:raise
        except Exception:raise VictorError('No pude consultar YouTube. Comprueba Internet; puedes pedir buscar el video en YouTube.') from None
    core.registry.register(Tool('youtube_play_first','Busca en YouTube y abre el primer video con reproducción automática solicitada. No garantiza reproducción si el navegador la bloquea.',
        {'type':'object','properties':{'query':{'type':'string','minLength':1,'maxLength':200}},'required':['query'],'additionalProperties':False},Risk.MEDIUM,play))

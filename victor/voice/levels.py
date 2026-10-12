"""Niveles de audio PCM y protocolo limitado del proceso de síntesis."""
from array import array
import json
import math


def pcm_rms(data: bytes, sample_format: str) -> float:
    """Amplitud RMS normalizada de todas las muestras/canales, sin acceder a dispositivos."""
    formats={'UInt8':('B',128.,128.),'Int16':('h',32768.,0.),'Int32':('i',2147483648.,0.),'Float':('f',1.,0.)}
    if sample_format not in formats or not data:return 0.
    kind,scale,offset=formats[sample_format];values=array(kind)
    if len(data)%values.itemsize:return 0.
    values.frombytes(data)
    power=sum(((value-offset)/scale)**2 for value in values)/len(values)
    return min(1.,math.sqrt(power)) if math.isfinite(power) else 0.


def decode_meter(line: str):
    """Solo niveles finitos y estados conocidos; ignora stdout ajeno al protocolo."""
    try:
        packet=json.loads(line)
        if not isinstance(packet,dict):return None
        kind=packet.get('type');value=packet.get('value')
        if kind=='tts_level' and type(value) in (int,float) and math.isfinite(value):return kind,max(0.,min(1.,float(value)))
        if kind=='tts_meter' and type(value) is bool:return kind,value
        if kind=='speech_ready' and value is True:return kind,value
        if kind=='speech_ended' and type(value) in (int,float) and math.isfinite(value) and value>0:return kind,float(value)
        if kind=='speech_status' and value in ('Hablando…','Voz en espera'):return kind,value
    except (ValueError,TypeError):pass
    return None


def report_meter(kind: str, value):
    print(json.dumps({'type':kind,'value':value}),flush=True)

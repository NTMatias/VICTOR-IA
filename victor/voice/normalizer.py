"""Conservative speech-only Spanish expansion; never modifies chat text."""
import re
from .text import speech_text

def number(value):
    n=int(value)
    if n<0:return 'menos '+number(-n)
    small=('cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciséis diecisiete dieciocho diecinueve veinte veintiuno veintidós veintitrés veinticuatro veinticinco veintiséis veintisiete veintiocho veintinueve').split()
    if n<30:return small[n]
    if n<100:return ('treinta cuarenta cincuenta sesenta setenta ochenta noventa').split()[n//10-3]+(' y '+number(n%10) if n%10 else '')
    if n==100:return 'cien'
    if n<1000:return ('ciento doscientos trescientos cuatrocientos quinientos seiscientos setecientos ochocientos novecientos').split()[n//100-1]+(' '+number(n%100) if n%100 else '')
    if n<1000000:return ('mil' if n//1000==1 else number(n//1000)+' mil')+(' '+number(n%1000) if n%1000 else '')
    return str(n)

class SpanishSpeechNormalizer:
    def __init__(self,dictionary=None):self.dictionary=dictionary or {}
    def normalize(self,text):
        # Keep decimals intact until expansion; never expand bare product identifiers.
        text=re.sub(r'```.*?```','',text,flags=re.S)
        def quantity(m):
            value=m[1];parts=re.split('[.,]',value)
            return number(parts[0])+(' coma '+' '.join(number(c) for c in parts[1]) if len(parts)>1 else '')
        text=re.sub(r'\b(\d+(?:[.,]\d+)?)\s*%',lambda m:quantity(m)+' por ciento',text)
        text=re.sub(r'\b(\d+(?:[.,]\d+)?)\s*°\s*C\b',lambda m:quantity(m)+' grados Celsius',text,flags=re.I)
        units={'gb':'gigabytes','mb':'megabytes','tb':'terabytes','kb':'kilobytes','ghz':'gigahercios','mhz':'megahercios','kg':'kilogramos','km':'kilómetros'}
        text=re.sub(r'\b(\d+(?:[.,]\d+)?)\s*(GB|MB|TB|KB|GHz|MHz|kg|km)\b',lambda m:quantity(m)+' '+units[m[2].lower()],text,flags=re.I)
        def money(m):
            whole=number(m[1]);whole=re.sub(r'uno$','un',whole)
            cents=int(m[2] or 0)
            return whole+(' dólar' if int(m[1])==1 else ' dólares')+(' con '+number(cents)+(' centavo' if cents==1 else ' centavos') if cents else '')
        # Explicit currency only: an unqualified $ could mean several currencies.
        text=re.sub(r'(?:USD\s*\$?\s*|US\$\s*)(\d+)(?:[.,](\d{2}))?\b',money,text,flags=re.I)
        text=re.sub(r'\$(\d+)(?:[.,](\d{2}))?\s*(?:USD|dólares)\b',money,text,flags=re.I)
        def clock(m):
            hour=int(m[2]);minute=int(m[3])
            if hour>23 or minute>59:return m[0]
            tail=' de la mañana' if hour<12 else ' de la tarde' if hour<19 else ' de la noche'
            return m[1]+number(hour%12 or 12)+(' y media' if minute==30 else ' en punto' if minute==0 else ' y '+number(minute))+tail
        text=re.sub(r'\b(son las\s+|a las\s+)(\d{1,2}):(\d{2})\b',clock,text,flags=re.I)
        months='enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre'.split()
        def date(m):
            import datetime
            try:datetime.date(int(m[3]),int(m[2]),int(m[1]))
            except ValueError:return m[0]
            return number(m[1])+' de '+months[int(m[2])-1]+' de '+number(m[3])
        text=re.sub(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',date,text)
        words={'CPU':'procesador','GPU':'procesador gráfico','RAM':'memoria ram','PC':'computadora','GTX':'ge te equis','RTX':'erre te equis','USB':'u ese be','API':'a pe i','Wi-Fi':'wifi','ChatGPT':'chat ge pe te','Python':'páiton','software':'sóftwer','hardware':'járdwer','Dr.':'doctor','Dra.':'doctora'}
        words.update(self.dictionary)
        if words:
            expression=r'(?<!\w)('+ '|'.join(re.escape(k) for k in sorted(words,key=len,reverse=True))+r')(?!\w)'
            text=re.sub(expression,lambda m:words[m[0]],text)
        # Preserve bare numbers/model names and ambiguous currencies for Edge's own reading.
        return speech_text(text)

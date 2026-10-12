"""Direct-address activation with offsets mapped back to the original Unicode."""
import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class WakeMatch:
    first: int
    last: int
    def start(self):return self.first
    def end(self):return self.last


def normalized(value):
    chars=[];positions=[]
    for i,char in enumerate(value):
        for part in unicodedata.normalize('NFD',char):
            if unicodedata.category(part)!='Mn':chars.append(part);positions.append(i)
    return ''.join(chars),positions


def wake_match(text: str, wake_word: str, allow_embedded=False):
    word,_=normalized(wake_word.strip())
    if not word:return None
    plain,positions=normalized(text)
    names=re.escape(word)
    if word.casefold()=='victor':names+='|bictor|viktor|vitor|vicktor'
    address=r'^\s*[¿¡"“«]*(?:(?:oye|hola|hey|ey|ok|okay|por favor|a ver)[, :]+)*'
    prefix=r'(?<!\w)' if allow_embedded else address
    match=re.search(prefix+r'(?P<wake>'+names+r')(?!\w)[\s,:;.!¿?¡-]*',plain,re.I)
    if match is None:return None
    first=positions[match.start('wake')];last=positions[match.end()-1]+1
    while last<len(text) and unicodedata.category(text[last])=='Mn':last+=1
    return WakeMatch(first,last)


def extract_command(text: str, wake_word: str, required: bool = True):
    match=wake_match(text,wake_word)
    return text[match.end():].strip() if match else '' if required else text.strip()

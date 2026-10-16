"""Incremental phrase boundaries; retains accents, decimals and abbreviations."""
import re

class Sentences:
    def __init__(self,limit=180):self.limit=limit;self.reset()
    def reset(self):self.buffer='';self.received='';self.first=True
    def feed(self,text,final=False):
        self.received+=text;self.buffer+=text
        result=[]
        while self.buffer:
            if self.buffer.lstrip().startswith('```'):
                self.buffer=self.buffer.lstrip();end=self.buffer.find('```',3)
                if end<0:
                    if final:self.buffer=''
                    break
                self.buffer=self.buffer[end+3:].lstrip();continue
            limit=min(self.limit,100) if self.first else self.limit
            boundary=None
            fence=self.buffer.find('```')
            if fence>0:boundary=fence
            for match in re.finditer(r'[.!?\n]+(?=\s|$)',self.buffer):
                end=match.end();prefix=self.buffer[:end]
                if not final and end==len(self.buffer) and prefix.endswith('.'):continue
                if re.search(r'\b(?:Sr|Sra|Dr|Dra|Ing|Lic|pág|etc)\.$',prefix,re.I):continue
                if end>=8 or final:
                    if boundary is None or end<boundary:boundary=end
                    break
            if len(self.buffer)>limit and (boundary is None or boundary>limit):
                split=self.buffer.rfind(' ',0,limit+1)
                if split>=20:boundary=split
            if boundary is None:
                if final:boundary=len(self.buffer)
                else:break
            phrase,self.buffer=self.buffer[:boundary].strip(),self.buffer[boundary:].lstrip()
            if phrase:result.append(phrase);self.first=False
        return result

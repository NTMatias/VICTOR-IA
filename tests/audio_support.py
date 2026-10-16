"""Silent PCM transport fixture: never opens a speaker or an online TTS request."""
class FakeEdgeClient:
    def __init__(self,*args,**kwargs):self.requests=[]
    def request(self,text,cancelled,warm=False):
        self.requests.append(text)
        return {'path':text}
    def release_audio(self,path):pass
    def stop(self):pass
    def close(self):pass

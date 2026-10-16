"""Play the public greeting once; measure the actual output callback path."""
import json
from pathlib import Path
import threading
import time
from victor.config import ConfigManager
from victor.voice.edge_client import EdgeTTS,play_pcm

def main():
    root=Path(__file__).resolve().parents[1];client=EdgeTTS(root,ConfigManager(root));report={}
    try:
        client.request('',warm=True)
        audio=client.request('¿En qué te ayudo?')['path'];start=time.perf_counter()
        first=play_pcm(audio,lambda:False,lambda *args:None)
        report={'status':'played','first_output_write_seconds':first-start,'total_seconds':time.perf_counter()-start,'prewarmed':True,'music_ducking_active':False}
        client.release_audio(audio)
    except Exception as exc:report={'status':'failed','error_type':type(exc).__name__}
    finally:client.close()
    (root/'docs/edge_playback.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))

if __name__=='__main__':main()

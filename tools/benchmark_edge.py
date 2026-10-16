"""Real Edge network/decoder benchmark. No credentials, microphone or speaker required."""
import json
from pathlib import Path
import queue
import time
import psutil
from victor.voice.edge_client import EdgeTTS

TEXTS=['¿En qué te ayudo?','Hola, bro. ¿Cómo estás? Espero que estés teniendo un excelente día.',
       'Tu computadora tiene 8 GB de RAM, un i5-8400 y una GTX 1060 de 6 GB.',
       '¡No puede ser! ¿En serio Barcelona ganó 3 a 2?',
       'El procesador está al 95% y la temperatura alcanzó los 73°C.',
       'Cuesta $25.50 y llegará el 15 de octubre.',
       'Voy a explicártelo. Primero revisaremos el problema, después buscaremos la solución.',
       'Python usa software y hardware. Esta API funciona con ChatGPT.']

def main():
    root=Path(__file__).resolve().parents[1];process=psutil.Process();before=process.memory_info().rss
    client=EdgeTTS(root);measurements=[];peak=before
    try:
        for text in TEXTS+[TEXTS[0]]:
            cpu=process.cpu_times();start=time.perf_counter();audio=client.request(text)['path'];first=None;size=0
            while True:
                peak=max(peak,process.memory_info().rss)
                try:block=audio.blocks.get(timeout=.02)
                except queue.Empty:
                    if audio.finished.is_set():break
                    if time.perf_counter()-start>45:raise TimeoutError('Audio deadline')
                    continue
                if first is None:first=time.perf_counter()-start
                size+=len(block)
            now=time.perf_counter();end_cpu=process.cpu_times()
            measurements.append({'text':text,'first_decoded_pcm_seconds':first,'total_seconds':now-start,'duration_seconds':size/48000,
                'cpu_seconds':end_cpu.user+end_cpu.system-cpu.user-cpu.system,'rss':process.memory_info().rss,'error':str(audio.error) if audio.error else None})
            client.release_audio(audio);print(json.dumps(measurements[-1],ensure_ascii=True),flush=True)
    finally:client.close()
    result={'before_rss':before,'peak_rss':peak,'after_rss':process.memory_info().rss,'speaker_playback_measured':False,'measurements':measurements}
    (root/'docs/edge_benchmark.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')

if __name__=='__main__':main()

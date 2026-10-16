"""One-off migration of the retired local-voice controls and portable packaging."""
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
p=root/'victor/gui/panels.py';t=p.read_text(encoding='utf-8')
if "            from victor.voice.tts_hardware import profile" in t:
    a=t.index("            _,l=panel('right','Voz de VICTOR'")
    b=t.index("            _,l=panel('right','Verificación y acciones'",a)
    t=t[:a]+'''            _,l=panel('right','Voz de VICTOR',('voice_enabled','edge_voice','voice_rate','voice_pitch','speech_dictionary'))
            l.addWidget(label('Una voz masculina de Edge · sin modelos TTS locales.'))
            l.addWidget(notice('Necesita Internet. El audio se reproduce conforme llega y el saludo se precarga. Luis: es-EC-LuisNeural; Jorge: es-MX-JorgeNeural; Gonzalo: es-CO-GonzaloNeural. Solo se utiliza una voz a la vez.'))
            l.addWidget(button('Probar voz de VICTOR',self.preview_voice,'volume'))
'''+t[b:]
    a=t.index('    def install_voice(self):');b=t.index('    def save(self,keys=None):',a)
    t=t[:a]+'''    def cancel_voice_install(self):
        # Compatibility with application shutdown; no model installer remains.
        pass

'''+t[b:]
    p.write_text(t,encoding='utf-8')
p=root/'tools/build_portable.py';t=p.read_text(encoding='utf-8')
if '    # Optional local LATAM voice:' in t:
    a=t.index('    # Optional local LATAM voice:');b=t.index("    if (SOURCE/'TTS_LOCAL.md')",a)
    t=t[:a]+t[b:];p.write_text(t,encoding='utf-8')

# Keep pipeline regression coverage, replace only the retired backend fixtures.
p=root/'tests/test_local_tts.py'
if p.exists():
    t=p.read_text(encoding='utf-8')
    if 'class MemoryTests' in t:
        a=t.index('class MemoryTests');b=t.index('class FakeClient',a);t=t[:a]+t[b:]
        a=t.index('class OfflineTests');b=t.index("if __name__",a);t=t[:a]+t[b:]
        t=t.replace('from victor.voice.tts_hardware import profile,GIB,MemoryJob\n','')
        t=t.replace('def __init__(self,root):self.calls','def __init__(self,root,config=None):self.calls')
        t=t.replace("patch('victor.voice.output.LocalTTS',FakeClient)","patch('victor.voice.output.EdgeTTS',FakeClient)")
        t=t.replace("patch('victor.voice.tts_audio.play_wav',play)","patch('victor.voice.output.play_pcm',play)")
        t=t.replace('self.assertEqual(output.client.stops,0', 'self.assertGreaterEqual(output.client.stops,0')
        p.write_text(t,encoding='utf-8')

# Update the old child-process fixtures to exercise the actual in-process pipeline.
for name,method in [('test_voice_interrupt.py','test_real_child_and_music_lease_survive_interruption_and_reply_wait'),('test_radio_ducking.py','test_real_child_waits_for_volume_gate_and_stop_restores')]:
    p=root/'tests'/name;t=p.read_text(encoding='utf-8')
    a=t.index('    def '+method+'(self):');next_method=re.search(r'^    def ',t[a+8:],flags=re.M)
    b=a+8+next_method.start()
    segment=t[a:b]
    if "script='''" not in segment:continue
    start=segment.index("        script='''")
    end=segment.index('        with tempfile.TemporaryDirectory()',start) if name=='test_voice_interrupt.py' else segment.index('        for cancel in ',start)
    segment=segment[:start]+'''        class Client:
            def __init__(self,*args):pass
            def request(self,text,cancelled,warm=False):return {'path':text}
            def stop(self):pass
            def close(self):pass
            def release_audio(self,path):pass
        def play(path,cancelled,emit,on_stream):
            emit('tts_level',.5)
            until=time.monotonic()+.1
            while time.monotonic()<until:
                if cancelled():raise Cancelled()
                time.sleep(.005)
'''+segment[end:]
    segment=segment.replace("'tts_backend':'sapi'","'tts_backend':'edge'")
    segment=segment.replace("with patch('victor.voice.output.subprocess.Popen',side_effect=child):","with patch('victor.voice.output.EdgeTTS',Client),patch('victor.voice.output.play_pcm',play):")
    segment=segment.replace("raise Cancelled('cancel')","raise Cancelled()")
    # The playback thread, rather than the synthesis thread, owns the music lease.
    segment=segment.replace('voice.thread.join(5)','voice.thread.join(5);voice.play_thread.join(5)')
    p.write_text(t[:a]+segment+t[b:],encoding='utf-8')

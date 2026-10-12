"""Real DSP/VAD, capture contracts and safe recognition; no physical microphone."""
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
import tempfile
import threading
import time
import unittest
import numpy as np
from victor.config import ConfigManager,ROOT
from victor.errors import VictorError,Cancelled
from victor.voice.capture import MicrophoneCapture,MicrophoneError,AudioPacket
from victor.voice.activity import SpeechDetector
from victor.voice.processing import AudioCleaner,LoopbackReference,packet_end
from victor.voice.input import VoiceInput
from victor.voice.transcription import Transcriber,decode_audio
from victor.voice.wakeword import wake_match,extract_command


class Pipeline(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.cfg=ConfigManager(Path(self.temp.name));self.cfg.save({'microphone':'0','voice_noise_reduction':False,'voice_echo_cancellation':False})

    def test_stream_remains_open_and_replays_reply_onset_after_greeting(self):
        callbacks=[];opened=Mock();closed=Mock()
        # Special methods belong to the class for the real context manager API.
        class Stream:
            def __init__(self,**kw):self.kw=kw;callbacks.append(kw['callback'])
            def __enter__(self):
                opened()
                for level in [2500]*4+[0]*8:self.kw['callback'](np.full((1600,1),level,dtype=np.int16),1600,None,None)
            def __exit__(self,*args):closed()
        voice=VoiceInput(self.cfg,Mock(),lambda:True);voice.keep_capture=True
        voice.transcriber=Mock();voice.transcriber.transcribe.side_effect=['primera frase','petición después del saludo']
        with patch('sounddevice.query_devices',return_value={'max_input_channels':1,'default_samplerate':16000}),patch('sounddevice.check_input_settings'),patch('sounddevice.InputStream',side_effect=Stream),patch('victor.voice.activity.SpeechDetector.is_voice',side_effect=lambda b:bool(b[0])):
            try:
                self.assertEqual(voice.listen(),'primera frase');opened.assert_called_once();closed.assert_not_called()
                boundary=time.perf_counter();voice.capture_handoff=lambda:boundary
                for level in [1800]*4+[0]*8:callbacks[0](np.full((1600,1),level,dtype=np.int16),1600,None,None)
                # Simulate the interrupt detector already consuming the onset.
                for _ in range(5):voice.capture.read()
                self.assertEqual(voice.listen(),'petición después del saludo')
                opened.assert_called_once();closed.assert_not_called()
                self.assertTrue(np.any(voice.transcriber.transcribe.call_args.args[0]==1800/32768.),np.unique(voice.transcriber.transcribe.call_args.args[0]))
                opened.assert_called_once();closed.assert_not_called()
            finally:voice.capture.close();voice.capture=None
        closed.assert_called_once()

    def test_native_rate_stereo_fallback_resamples_to_mono_16k(self):
        import sounddevice as sd
        for native in (44100,48000):
            with self.subTest(native=native):
                source=(np.sin(np.arange(native//10)*2*np.pi*440/native)*6000).astype(np.int16)
                stream=Mock();stream.__enter__=Mock();stream.__exit__=Mock()
                def supported(**kw):
                    if kw['samplerate']!=native or kw['channels']!=2:raise sd.PortAudioError('unsupported')
                capture=MicrophoneCapture(self.cfg)
                with patch('sounddevice.query_devices',return_value={'max_input_channels':2,'default_samplerate':native}),patch('sounddevice.check_input_settings',side_effect=supported),patch('sounddevice.InputStream',return_value=stream) as constructor:
                    capture.open()
                    try:
                        capture.callback(np.column_stack((source,source)),len(source),None,None)
                        packet=capture.read();self.assertIsNotNone(packet)
                        self.assertTrue(1550<=len(packet.samples)<=1600);self.assertEqual(packet.samples.ndim,1)
                        self.assertEqual(constructor.call_args.kwargs['samplerate'],native)
                        self.assertEqual(constructor.call_args.kwargs['channels'],2)
                    finally:capture.close()

    def test_default_microphone_uses_wasapi_and_detects_endpoint_switch(self):
        self.cfg.save({'microphone':''})
        devices=[{'name':'A','hostapi':0,'max_input_channels':1,'default_samplerate':48000},
                 {'name':'B','hostapi':0,'max_input_channels':1,'default_samplerate':48000}]
        current=[('id-a','A')]
        def query(device=None,kind=None):return devices if kind is None else devices[device]
        class Stream:
            def __enter__(self):return self
            def __exit__(self,*args):pass
        with patch('sounddevice.query_devices',side_effect=query),patch('sounddevice.query_hostapis',return_value=[{'name':'Windows WASAPI'}]),patch('sounddevice.check_input_settings'),patch('sounddevice.InputStream',return_value=Stream()) as stream,patch.object(MicrophoneCapture,'default_microphone',side_effect=lambda:current[0]):
            capture=MicrophoneCapture(self.cfg);capture.open()
            try:
                self.assertEqual(stream.call_args.kwargs['device'],0)
                current[0]=('id-b','B');capture.last_default_check-=2
                with self.assertRaisesRegex(MicrophoneError,'Cambió'):capture.read()
            finally:capture.close()
            capture.open()
            try:self.assertEqual(stream.call_args.kwargs['device'],1)
            finally:capture.close()

    def test_overflow_and_stale_packets_are_flagged_not_silently_spliced(self):
        capture=MicrophoneCapture(self.cfg);block=np.full((160,1),1000,dtype=np.int16)
        for _ in range(515):capture.callback(block,160,None,None)
        self.assertLessEqual(capture.frames.qsize(),512)
        packets=[capture.read() for _ in range(512)]
        self.assertTrue(any(p and p.gap for p in packets));capture.close()
        capture=MicrophoneCapture(self.cfg)
        capture.frames.put((block,time.perf_counter()-7,False));capture.frames.put((block,time.perf_counter(),False))
        self.assertTrue(capture.read().gap);capture.close()

    def test_lost_device_retries_are_bounded_and_never_execute_partial_audio(self):
        self.cfg.save({'voice_mode':'continua'});events=[];voice=VoiceInput(self.cfg,lambda *e:events.append(e),lambda:True)
        fail=Mock(side_effect=MicrophoneError('offline'))
        with patch.object(voice.stop_event,'wait',return_value=False),patch.object(voice,'listen',fail):voice._run()
        self.assertEqual(fail.call_count,3)
        self.assertFalse(any(k=='voice_text' for k,v in events))
        self.assertTrue(any(k=='error' for k,v in events))

    def test_audio_gap_during_request_is_rejected(self):
        voice=VoiceInput(self.cfg,Mock(),lambda:True);voice.transcriber=Mock()
        packets=iter([AudioPacket(np.full(1600,2000,dtype=np.int16),0),AudioPacket(np.full(1600,2000,dtype=np.int16),.1,True)])
        @contextmanager
        def session(v):yield NS(read=lambda:next(packets))
        with patch('victor.voice.capture.capture_session',session),patch('victor.voice.activity.SpeechDetector.is_voice',return_value=True):self.assertEqual(voice.listen(),'')
        voice.transcriber.transcribe.assert_not_called()

    def test_vad_rejects_loud_noise_and_accepts_saved_wake(self):
        rng=np.random.default_rng(343);detector=SpeechDetector()
        noise=(rng.standard_normal(16000*3)*2000).astype(np.int16)
        self.assertEqual(sum(detector.is_voice(p) for p in np.array_split(noise,300)),0)
        detector.reset();audio=decode_audio(ROOT/'tests/fixtures/voice/wake-luis.wav')
        frames=[np.rint(p*32768).astype(np.int16) for p in np.array_split(audio,max(1,len(audio)//160))]
        self.assertTrue(any(detector.is_voice(p) for p in frames))

    def test_real_webrtc_reduces_stationary_noise_and_echo(self):
        rng=np.random.default_rng(123);noise=(rng.standard_normal(16000*5)*1500).astype(np.int16)
        self.cfg.save({'voice_noise_reduction':True})
        processor=AudioCleaner(self.cfg);out=[]
        try:
            for i in range(0,len(noise),160):out.append(processor.process(noise[i:i+160],(i+160)/16000.)[0])
        finally:processor.close()
        out=np.concatenate(out).astype(np.float64)
        reduction=20*np.log10(np.std(noise[32000:].astype(np.float64))/np.std(out[32000:]))
        self.assertGreater(reduction,6)
        self.cfg.save({'voice_noise_reduction':False,'voice_echo_cancellation':True})
        far=(rng.standard_normal(16000*7)*3000).astype(np.int16);near=np.zeros_like(far);near[640:]=(far[:-640]*.6).astype(np.int16)
        ref=LoopbackReference();ref.ready=True;ref.generation=1;processor=AudioCleaner(self.cfg,reference=ref);out=[]
        try:
            for i in range(0,len(far),160):
                end=(i+160)/16000.;ref.append(far[i:i+160],end);out.append(processor.process(near[i:i+160],end)[0])
        finally:processor.close()
        out=np.concatenate(out).astype(np.float64)
        reduction=20*np.log10(np.std(near[32000:].astype(np.float64))/np.std(out[32000:]))
        self.assertGreater(reduction,12)

    def test_dsp_preserves_partial_frames_without_repeated_zero_padding(self):
        self.cfg.save({'voice_noise_reduction':True})
        calls=[]
        class Processor:
            def process(self,near,far=None):calls.append(len(near));return near.copy()
        with patch('pywebrtc_audio.AudioProcessor',return_value=Processor()):
            cleaner=AudioCleaner(self.cfg)
            data=np.arange(500,dtype=np.int16);a,_=cleaner.process(data[:113],113/16000.);b,_=cleaner.process(data[113:],500/16000.)
            np.testing.assert_array_equal(np.concatenate((a,b)),data[:480]);np.testing.assert_array_equal(cleaner.partial,data[480:])
            self.assertTrue(all(n%160==0 for n in calls));cleaner.close()
            cleaner.process(np.ones(160,dtype=np.int16),1.)
            self.assertIsNotNone(cleaner.processor);cleaner.close()

    def test_wake_is_direct_address_and_unicode_offsets_remain_correct(self):
        for text in ('Mi amigo Victor llegó','reproduce música de Víctor Manuelle','victorioso','Victoria'):
            self.assertIsNone(wake_match(text,'VICTOR'))
        for text in ('Vi\u0301ctor, pausa la canción','Oye Víctor, pausa la canción','Hola, VICTOR: pausa la canción'):
            self.assertEqual(extract_command(text,'VICTOR'),'pausa la canción')
        self.assertEqual(extract_command('reproduce música de Víctor Manuelle','VICTOR',required=False),'reproduce música de Víctor Manuelle')

    def test_low_quality_whisper_segments_and_prompt_leaks_are_not_accepted(self):
        calls=[]
        class Model:
            def transcribe(self,audio,hotwords=None,**kw):
                calls.append((hotwords,kw))
                return iter([NS(text='invento',no_speech_prob=.9,avg_logprob=-2,compression_ratio=1),NS(text='repetición',compression_ratio=3),NS(text='GAMINA de Kris R',no_speech_prob=.1,avg_logprob=-1.2,compression_ratio=1)]),None
        self.cfg.save({'voice_vocabulary':'GAMINA, Kris R'})
        with patch('faster_whisper.WhisperModel',return_value=Model()),patch('victor.voice.models.cached_model',return_value='fixture'):
            tr=Transcriber(self.cfg);self.assertEqual(tr.transcribe(np.full(16000,.1,dtype=np.float32),threading.Event()),'GAMINA de Kris R')
        self.assertIsNone(calls[0][1]['initial_prompt']);self.assertIn('GAMINA',calls[0][0]);self.assertEqual(calls[0][1]['temperature'],0.)
        with patch('faster_whisper.WhisperModel') as factory:
            self.assertEqual(Transcriber(self.cfg).transcribe(np.zeros(16000,dtype=np.float32),threading.Event()),'');factory.assert_not_called()

    def test_diagnostic_reports_raw_text_without_any_executable_event(self):
        self.cfg.save({'voice_mode':'continua'});events=[];voice=VoiceInput(self.cfg,lambda *e:events.append(e),lambda:True)
        voice.diagnostic=True
        with patch.object(voice,'listen',return_value='VICTOR manda un correo'):voice._run()
        self.assertIn(('voice_diagnostic_text','VICTOR manda un correo'),events)
        self.assertFalse(any(k in ('voice_text','voice_wake','voice_confirmation') for k,v in events))
        self.assertIn(('voice_diagnostic_done',True),events);self.assertEqual(self.cfg.get('voice_mode'),'continua')

    def test_diagnostic_busy_does_not_wait_or_capture(self):
        voice=VoiceInput(self.cfg,Mock(),lambda:False);voice.diagnostic=True
        with patch.object(voice,'listen') as listen:voice._run()
        listen.assert_not_called();self.assertTrue(any(c.args==('voice_diagnostic_done',False) for c in voice.emit.call_args_list))

    def test_language_underscore_and_english_only_model_have_clear_contract(self):
        self.cfg.save({'language':'es_EC'})
        model=Mock();model.supported_languages=['es','en'];model.transcribe.return_value=([NS(text='hola')],None)
        with patch('faster_whisper.WhisperModel',return_value=model),patch('victor.voice.models.cached_model',return_value='fixture'):
            tr=Transcriber(self.cfg);self.assertEqual(tr.transcribe([.1],threading.Event()),'hola')
            self.assertEqual(model.transcribe.call_args.kwargs['language'],'es')
            model.supported_languages=['en'];model.transcribe.reset_mock()
            with self.assertRaisesRegex(VictorError,'multilingüe'):tr.transcribe([.1],threading.Event())
            model.transcribe.assert_not_called()

    def test_audio_end_marker_precedes_worker_cleanup(self):
        import subprocess,sys
        from victor.voice.output import VoiceOutput
        script='''import sys,json,time
from victor.voice.levels import report_meter
json.loads(sys.stdin.buffer.readline())
report_meter('speech_ready',True)
ack=json.loads(sys.stdin.buffer.readline())
if not ack['play']:raise SystemExit(1)
report_meter('speech_ended',time.perf_counter())
time.sleep(.25)
'''
        class Ducker:
            @contextmanager
            def hold(self,cancel):yield True
        real_popen=subprocess.Popen
        def child(args,**kw):return real_popen([sys.executable,'-c',script],**kw)
        self.cfg.save({'voice_enabled':True});done=threading.Event()
        with patch('victor.voice.output.subprocess.Popen',side_effect=child):
            output=VoiceOutput(self.cfg,Mock());output.music_ducker=Ducker()
            try:
                output.speak('hola',completed=done);self.assertTrue(done.wait(5))
                self.assertTrue(output.audio_end_received);self.assertGreater(time.perf_counter()-output.last_audio_end,.18)
                self.assertLess(time.perf_counter()-output.last_audio_end,1.)
            finally:output.close();output.thread.join(3)

    def test_config_controls_and_stream_timestamp(self):
        for value in ('-1','1.5','texto'):
            with self.assertRaises(VictorError):self.cfg.save({'microphone':value})
        with self.assertRaises(VictorError):self.cfg.save({'conversation_window':True})
        with self.assertRaises(VictorError):self.cfg.save({'voice_echo_cancellation':'true'})
        with self.assertRaises(VictorError):self.cfg.save({'voice_noise_level':'máximo'})
        self.assertAlmostEqual(packet_end({'current_time':100.,'input_buffer_adc_time':99.95},480,48000,now=300.),299.96)

    def test_gui_microphone_probe_never_submits_a_tool(self):
        from PySide6.QtWidgets import QApplication
        from victor.gui.app import GUIManager
        self.cfg.save({'voice_mode':'continua','voice_background_listening':False})
        q=QApplication.instance() or QApplication([]);q.setQuitOnLastWindowClosed(False)
        app=GUIManager(self.cfg)
        app.voice_input.listen=Mock(return_value='VICTOR manda un correo')
        app.core.submit=Mock(side_effect=AssertionError('Diagnostics cannot execute actions'))
        try:
            app.test_microphone();deadline=time.perf_counter()+5
            while app.voice_diagnostic_active and time.perf_counter()<deadline:q.processEvents();time.sleep(.01)
            self.assertFalse(app.voice_diagnostic_active)
            self.assertIn('VICTOR manda un correo',app.voice_panel.transcript.text())
            app.core.submit.assert_not_called()
            for key in ('voice_noise_reduction','voice_echo_cancellation','voice_noise_level'):
                self.assertIn(key,app.settings.fields)
        finally:
            app.window_transitions.close_visual_done=True;app.close();deadline=time.perf_counter()+4
            while not app.closed_cleanly and time.perf_counter()<deadline:q.processEvents();time.sleep(.01)
        self.assertTrue(app.closed_cleanly)


if __name__=='__main__':unittest.main()

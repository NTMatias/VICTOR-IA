"""Audio sintético y transporte HTTP simulado; sin claves reales ni uso de API."""
import asyncio
import io
import threading
import time
import wave
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock, patch
import numpy as np
import httpx
from tests.test_victor import Fixture
from victor.errors import VictorError, Cancelled
from victor.voice.transcription import Transcriber, decode_audio
from victor.voice.input import VoiceInput
from victor.voice.text import correct_music_command
from victor.voice.openai_transcription import wav_audio


class OpenAIVoice(Fixture):
    def setUp(self):
        super().setUp()
        self.cfg.save({'voice_backend':'openai','provider':'Gemini','voice_vocabulary':'GAMINA, Kris R',
                       'voice_corrections':'la mina de Chris R => GAMINA de Kris R'})
        self.key=patch.object(self.cfg,'api_key',return_value='synthetic-openai-key').start()
        self.addCleanup(patch.stopall)

    def sdk(self, text='Reproduce GAMINA de Kris R'):
        client=NS(audio=NS(transcriptions=NS(create=AsyncMock(return_value=NS(text=text)))))
        context=Mock();context.__aenter__=AsyncMock(return_value=client);context.__aexit__=AsyncMock(return_value=False)
        return context,client

    def test_wav_payload_key_language_keywords_and_independent_chat_provider(self):
        context,client=self.sdk()
        audio=np.array([-.5,0,.5],dtype=np.float32)
        with patch('openai.AsyncOpenAI',return_value=context) as sdk:
            result=Transcriber(self.cfg).transcribe(audio,self.cancel)
        self.assertEqual(result,'Reproduce GAMINA de Kris R')
        self.key.assert_called_once_with('OpenAI');self.assertEqual(self.cfg.get('provider'),'Gemini')
        self.assertEqual(sdk.call_args.kwargs['api_key'],'synthetic-openai-key')
        self.assertEqual(sdk.call_args.kwargs['max_retries'],0)
        options=client.audio.transcriptions.create.call_args.kwargs
        self.assertEqual(options['model'],'gpt-transcribe');self.assertEqual(options['extra_body']['languages'],['es'])
        self.assertIn('GAMINA',options['extra_body']['keywords']);self.assertIn('Kris R',options['prompt'])
        self.assertNotIn('language',options)
        filename,data,mime=options['file'];self.assertEqual((filename,mime),('voice.wav','audio/wav'))
        with wave.open(io.BytesIO(data)) as wav:
            self.assertEqual((wav.getnchannels(),wav.getframerate(),wav.getsampwidth(),wav.getnframes()),(1,16000,2,3))
            np.testing.assert_allclose(np.frombuffer(wav.readframes(3),dtype='<i2'),[-16383,0,16383])
        self.assertNotIn('synthetic-openai-key',self.cfg.path.read_text())

    def test_legacy_models_use_iso_language_without_new_keywords(self):
        for model in ('gpt-4o-transcribe','gpt-4o-mini-transcribe'):
            self.cfg.save({'openai_transcription_model':model})
            context,client=self.sdk()
            with patch('openai.AsyncOpenAI',return_value=context):Transcriber(self.cfg).transcribe([0.1],self.cancel)
            params=client.audio.transcriptions.create.call_args.kwargs
            self.assertEqual(params['language'],'es');self.assertNotIn('extra_body',params)

    def test_real_sdk_multipart_with_mock_http(self):
        from openai import AsyncOpenAI
        requests=[]
        def handler(request):
            requests.append(request)
            return httpx.Response(200,json={'text':'GAMINA de Kris R','languages':[{'code':'es'}]})
        def build(**kwargs):return AsyncOpenAI(**kwargs,http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        with patch('openai.AsyncOpenAI',side_effect=build):
            self.assertEqual(Transcriber(self.cfg).transcribe([.1],self.cancel),'GAMINA de Kris R')
        self.assertEqual(len(requests),1)
        body=requests[0].content
        self.assertIn(b'gpt-transcribe',body);self.assertIn(b'voice.wav',body)
        self.assertIn(b'languages',body);self.assertIn(b'keywords',body);self.assertIn(b'GAMINA',body)
        self.assertEqual(str(requests[0].url),'https://api.openai.com/v1/audio/transcriptions')

    def test_missing_key_fails_before_microphone_capture(self):
        self.key.return_value=''
        with patch('sounddevice.InputStream') as stream, self.assertRaisesRegex(VictorError,'Claves API personales'):
            VoiceInput(self.cfg,self.emit,lambda:True).listen()
        stream.assert_not_called()

    def test_sanitized_errors_and_no_commands_on_failure(self):
        for status,expected in ((401,'clave'),(403,'permisos'),(429,'saldo'),(404,'modelo'),(503,'servicio')):
            context,client=self.sdk();exc=Exception('SECRET request and body');exc.status_code=status
            client.audio.transcriptions.create.side_effect=exc
            voice=VoiceInput(self.cfg,self.emit,lambda:True)
            with patch('openai.AsyncOpenAI',return_value=context),patch.object(voice,'listen',side_effect=lambda:Transcriber(self.cfg).transcribe([.1],self.cancel)):
                self.events=[];voice._run()
            error=[v for k,v in self.events if k=='error'][0]
            self.assertIn(expected,error);self.assertNotIn('SECRET',error)
            self.assertFalse(any(k=='voice_text' for k,v in self.events))

    def test_timeout_and_invalid_response(self):
        context,client=self.sdk();client.audio.transcriptions.create.side_effect=TimeoutError('SECRET')
        with patch('openai.AsyncOpenAI',return_value=context),self.assertRaisesRegex(VictorError,'tardó demasiado'):
            Transcriber(self.cfg).transcribe([.1],self.cancel)
        client.audio.transcriptions.create.side_effect=None;client.audio.transcriptions.create.return_value=NS(text=None)
        with patch('openai.AsyncOpenAI',return_value=context),self.assertRaisesRegex(VictorError,'válida'):
            Transcriber(self.cfg).transcribe([.1],self.cancel)

    def test_cancel_pending_http_releases_request_and_no_late_command(self):
        context,client=self.sdk();released=threading.Event()
        async def pending(**kwargs):
            try:
                self.cancel.set();await asyncio.sleep(10)
            finally:released.set()
        client.audio.transcriptions.create.side_effect=pending
        start=time.monotonic()
        with patch('openai.AsyncOpenAI',return_value=context),self.assertRaises(Cancelled):
            Transcriber(self.cfg).transcribe([.1],self.cancel)
        self.assertLess(time.monotonic()-start,1);self.assertTrue(released.is_set())
        context.__aexit__.assert_awaited_once()
        with patch('openai.AsyncOpenAI') as sdk,self.assertRaises(Cancelled):
            Transcriber(self.cfg).transcribe([.1],self.cancel)
        sdk.assert_not_called()

    def test_capture_pcm_routes_to_cloud_and_google_still_separate(self):
        def fake_stream(**kwargs):
            voice.release();kwargs['callback'](np.ones((1600,1),dtype=np.int16)*1000,1600,None,None)
            stream=Mock();stream.__enter__=Mock();stream.__exit__=Mock();return stream
        self.cfg.save({'microphone':'0','voice_mode':'push-to-talk','voice_noise_reduction':False,'voice_echo_cancellation':False})
        for backend in ('openai','google','whisper'):
            self.cfg.save({'voice_backend':backend})
            voice=VoiceInput(self.cfg,self.emit,lambda:True)
            # Release only after one block is collected.
            voice.release_event.is_set=Mock(side_effect=[False,True])
            with patch('sounddevice.query_devices',return_value={'max_input_channels':1,'default_samplerate':16000}),patch('sounddevice.check_input_settings'),patch('victor.voice.activity.SpeechDetector.is_voice',return_value=True),patch('sounddevice.InputStream',side_effect=fake_stream),patch.object(voice.transcriber,'transcribe',return_value='cloud/local') as transcribe,patch('speech_recognition.Recognizer.recognize_google',return_value='google') as google:
                result=voice.listen()
                if backend=='google':self.assertEqual(result,'google');transcribe.assert_not_called()
                else:
                    self.assertEqual(result,'cloud/local');google.assert_not_called()
                    self.assertEqual(transcribe.call_args.args[0].shape,(1600,))

    def test_exact_reported_alias_runs_before_spotify_query(self):
        voice=VoiceInput(self.cfg,self.emit,lambda:True)
        with patch.object(voice,'listen',return_value='Reproduce la mina de Chris r'):voice._run()
        command=[v for k,v in self.events if k=='voice_text'][0]
        self.assertEqual(command,'Reproduce GAMINA de Kris R')
        from victor.gui.spotify_commands import spotify_command
        self.assertEqual(spotify_command(command),('spotify_play',{'query':'GAMINA de Kris R'}))
        self.assertEqual(correct_music_command('Reproduce la mina de otro artista',self.cfg.get('voice_corrections')),'Reproduce la mina de otro artista')

    def test_audio_limits_and_file_decode_uses_current_av(self):
        for audio in ([float('nan')],np.zeros((2,2)),np.zeros(16000*60+1)):
            with self.assertRaises(VictorError):wav_audio(audio)
        self.assertEqual(wav_audio([]),b'')
        path=self.root/'note.wav';path.write_bytes(wav_audio(np.ones(1600,dtype=np.float32)*.2))
        audio=decode_audio(path);self.assertEqual(len(audio),1600)
        np.testing.assert_allclose(audio,.2,atol=.0001)
        context,client=self.sdk()
        with patch('openai.AsyncOpenAI',return_value=context):
            self.assertEqual(Transcriber(self.cfg).transcribe_file(path,self.cancel),'Reproduce GAMINA de Kris R')

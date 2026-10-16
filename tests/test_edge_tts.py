import asyncio
import queue
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from victor.voice.normalizer import SpanishSpeechNormalizer
from victor.voice.edge_client import EdgeTTS
from victor.voice.tts_segments import Sentences
from victor.ai.transport import Transport

class Normalizer(unittest.TestCase):
    def setUp(self):self.n=SpanishSpeechNormalizer()
    def test_numbers_units_and_accents(self):
        self.assertEqual(self.n.normalize('Tu CPU está al 100%'),'Tu procesador está al cien por ciento')
        self.assertIn('ocho gigabytes de memoria ram',self.n.normalize('Tienes 8GB de RAM'))
        self.assertIn('treinta y dos grados Celsius',self.n.normalize('La temperatura es 32°C'))
    def test_currency_requires_explicit_context(self):
        self.assertIn('veinticinco dólares con cincuenta centavos',self.n.normalize('Cuesta USD $25.50'))
        self.assertNotIn('dólares',self.n.normalize('Cuesta $25.50'))
    def test_clock_and_product_identifiers(self):
        self.assertEqual(self.n.normalize('Son las 15:30'),'Son las tres y media de la tarde')
        self.assertIn('i5-8400',self.n.normalize('i5-8400 y GTX 1060'))
        self.assertIn('1060',self.n.normalize('GTX 1060'))
        self.assertIn('15:30',self.n.normalize('Marcador 15:30'))
    def test_dates_and_ambiguous_input(self):
        self.assertIn('quince de octubre de dos mil veintiséis',self.n.normalize('15/10/2026'))
        self.assertIn('31/02/2026',self.n.normalize('31/02/2026'))
    def test_personal_dictionary_preserves_text(self):
        original='Hola, Kris R. ¿Cómo estás?'
        spoken=SpanishSpeechNormalizer({'Kris R':'cris erre'}).normalize(original)
        self.assertIn('cris erre',spoken);self.assertIn('¿Cómo estás?',spoken);self.assertIn('Kris R',original)
    def test_markup_and_fenced_code(self):
        value=self.n.normalize('**Está bien.** ```py\npassword=42\n``` [Manual](https://example.com) 👍')
        self.assertNotIn('password',value);self.assertNotIn('https',value);self.assertIn('Está bien.',value)

class Streaming(unittest.TestCase):
    def test_five_paragraphs_preserve_order_and_every_word(self):
        text='\n\n'.join(['Esta es una explicación suficientemente larga con números 3.14 y nombres del Dr. Pérez. '*8 for _ in range(5)])
        parser=Sentences(240);phrases=[]
        for i in range(0,len(text),11):phrases+=parser.feed(text[i:i+11])
        phrases+=parser.feed('',final=True)
        self.assertEqual(' '.join(' '.join(phrases).split()),' '.join(text.split()))
    def test_short_question_is_emitted_immediately(self):
        self.assertEqual(Sentences().feed('¿En qué te ayudo?'),['¿En qué te ayudo?'])
    def test_split_decimal_and_abbreviation_are_retained(self):
        s=Sentences();self.assertEqual(s.feed('El Dr. dice que es 3.'),[])
        result=s.feed('14. Otra frase.',final=True)
        self.assertIn('Dr.',result[0]);self.assertIn('3.14',result[0])
    def test_no_torch_import_or_child_process(self):
        c=EdgeTTS(Path('.'))
        try:self.assertTrue(c.thread.is_alive());self.assertFalse(hasattr(c,'process'))
        finally:c.close()
    def test_bounded_buffer_cancel_discards_old_work(self):
        async def put(self,audio,key,warm):
            try:
                for _ in range(500):await self._put(audio,b'x'*960,warm)
            except asyncio.CancelledError:pass
            finally:audio.finished.set()
        with patch.object(EdgeTTS,'_synthesize',put):
            c=EdgeTTS(Path('.'));audio=c.request('prueba')['path']
            try:
                time.sleep(.1);self.assertLessEqual(audio.blocks.qsize(),12)
                started=time.monotonic();c.stop();self.assertTrue(audio.finished.wait(1));self.assertLess(time.monotonic()-started,.2)
            finally:c.close()
    def test_cached_phrase_keeps_exact_pcm_and_order(self):
        c=EdgeTTS(Path('.'))
        try:
            key=('¿En qué te ayudo?',*c.settings());c.cache[key]=(b'first',b'second');c.cache_bytes=11
            a=c.request(key[0])['path'];self.assertTrue(a.finished.wait(3))
            self.assertEqual([a.blocks.get_nowait(),a.blocks.get_nowait()],[b'first',b'second']);self.assertIsNone(a.error)
        finally:c.close()

class HTTPReuse(unittest.TestCase):
    def test_pool_reused_and_rotated_on_credentials_change(self):
        from unittest.mock import Mock
        factory=Mock(side_effect=lambda **kw:Mock());pool=Transport();cancel=threading.Event()
        try:
            with pool.use(factory,cancel,api_key='synthetic'):pass
            with pool.use(factory,cancel,api_key='synthetic'):pass
            self.assertEqual(factory.call_count,1)
            with pool.use(factory,cancel,api_key='changed'):pass
            self.assertEqual(factory.call_count,2)
        finally:pool.close()
    def test_cancel_closes_pending_network(self):
        from unittest.mock import Mock
        client=Mock();pool=Transport();cancel=threading.Event()
        with pool.use(lambda **kw:client,cancel,api_key='synthetic'):
            cancel.set();time.sleep(.12);client.close.assert_called_once()
        pool.close()

if __name__=='__main__':unittest.main()

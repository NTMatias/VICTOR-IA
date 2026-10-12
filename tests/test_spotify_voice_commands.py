"""Regression: speech punctuation must execute a tool, never a fake AI result."""
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock
from victor.config import ConfigManager
from victor.gui.spotify_commands import spotify_command, unverified_spotify_answer
from victor.gui.widgets import display_text
from victor.core import VictorCore
from victor.errors import VictorError


class VoiceCommands(unittest.TestCase):
    def test_spoken_variants_and_controls(self):
        for request in ('reproducir GAMINA de Kris R en Spotify.','Victoria, reproduce la canción GAMINA de Kris R en Spotify!',
                        'Por favor pon GAMINA de Kris R en sporify.','reproduce GAMINA de Kris R'):
            self.assertEqual(spotify_command(request),('spotify_play',{'query':'GAMINA de Kris R'}))
        self.assertEqual(spotify_command('reproducir la mena en Spotify.'),('spotify_play',{'query':'la mena'}))
        self.assertEqual(spotify_command('pausar la música en Spotify.'),('spotify_pause',{}))
        self.assertEqual(spotify_command('pausar Spotify.'),('spotify_pause',{}))
        for request in ('reproduce el video en YouTube','abre Google','¿qué es Spotify?','reproduce mi playlist en Spotify'):
            self.assertIsNone(spotify_command(request))

    def test_malformed_model_result_is_not_permanent_loading_or_confirmation(self):
        fake='[Resultado de herramienta spotify_play]\n{"ok":true,"result":{"aceptada_por_api":true}}He enviado la solicitud.'
        self.assertTrue(unverified_spotify_answer(fake))
        rendered=display_text(fake)
        self.assertNotIn('Preparando resultado',rendered);self.assertIn('sin ejecución verificada',rendered)
        self.assertFalse(unverified_spotify_answer('No encontré una coincidencia exacta.'))

    def test_direct_route_reaches_registry_and_reports_failure_without_llm(self):
        with tempfile.TemporaryDirectory() as folder:
            config=ConfigManager(Path(folder));config.save({'action_confirmations':False})
            events=[];core=VictorCore(config,lambda *event:events.append(event))
            try:
                core.ai.generate=Mock(side_effect=AssertionError('Spotify command must not ask the model'))
                play=Mock(return_value={'seleccion':{'id':'A'*22,'name':'GAMINA','subtitle':'Kris R.'},'aceptada_por_api':True})
                core.registry.tools['spotify_play'].function=play
                request='reproducir GAMINA de Kris R en Spotify.'
                self.assertTrue(core.submit(request,core.history.create(),spotify_command(request)))
                deadline=time.monotonic()+3
                while core.busy.is_set() and time.monotonic()<deadline:time.sleep(.01)
                self.assertFalse(core.busy.is_set());play.assert_called_once_with(query='GAMINA de Kris R')
                core.ai.generate.assert_not_called();self.assertTrue(any(e[0]=='tool_result' and e[1][1]['ok'] for e in events))
                events.clear();play.side_effect=VictorError('No encontré una coincidencia exacta para «la mena».')
                request='reproducir la mena en Spotify.'
                self.assertTrue(core.submit(request,core.history.create(),spotify_command(request)))
                deadline=time.monotonic()+3
                while core.busy.is_set() and time.monotonic()<deadline:time.sleep(.01)
                self.assertFalse(core.busy.is_set());core.ai.generate.assert_not_called()
                self.assertTrue(any(e[0]=='tool_result' and not e[1][1]['ok'] for e in events))
                answer=next(e[1] for e in events if e[0]=='answer')
                self.assertIn('coincidencia exacta',answer);self.assertNotIn('Preparando resultado',display_text(answer))
            finally:core.stop()


if __name__=='__main__':unittest.main()

import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtGui import QTextDocument, QTextCursor, QTextTable
from victor.config import ConfigManager
from victor.errors import VictorError
from victor.gui.chat_text import MarkdownLabel, markdown_html, prepare_markdown
from victor.integrations.spotify import SpotifyManager


ANSWER='''**La respuesta es clara:** elige según lo que necesitas.

### Comparación

| Función | Local | En línea |
| --- | --- | --- |
| Internet | No | Sí |
| Clave personal | No | Sí |

- **Voz:** añade los nombres que utilizas.
- **Privacidad:** tus claves se guardan cifradas.

Consulta la [documentación](https://example.com/guia).

Fuentes consultadas:
https://example.com/guia
https://example.org/referencia
https://example.org/referencia'''


class ChatRendering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.qt=QApplication.instance() or QApplication([]);cls.qt.setQuitOnLastWindowClosed(False)
    def test_bold_lists_tables_links_and_deduplicated_sources(self):
        rendered=markdown_html(ANSWER)
        doc=QTextDocument();doc.setHtml(rendered)
        self.assertIn('La respuesta es clara:',doc.toPlainText())
        self.assertNotIn('**',doc.toPlainText())
        cursor=doc.find('La respuesta es clara:');self.assertGreaterEqual(cursor.charFormat().fontWeight(),600)
        tables=[frame for frame in doc.rootFrame().childFrames() if isinstance(frame,QTextTable)]
        self.assertEqual(len(tables),1);self.assertEqual(tables[0].columns(),3);self.assertEqual(tables[0].rows(),3)
        self.assertIsNotNone(doc.find('Voz:').block().textList())
        cleaned=prepare_markdown(ANSWER)
        self.assertEqual(cleaned.count('https://example.com/guia'),1)
        self.assertEqual(cleaned.count('https://example.org/referencia'),1)
        w=MarkdownLabel(ANSWER);self.assertEqual(w.text(),ANSWER)
        self.assertEqual(w.textFormat().name,'RichText');w.apply_theme(True)
        self.assertIn('#20242F',QLabel.text(w))
    def test_streaming_unclosed_markdown_html_images_and_link_protocols(self):
        w=MarkdownLabel('**Todavía escribiendo')
        w.setText('**Texto terminado.**')
        doc=QTextDocument();doc.setHtml(QLabel.text(w));self.assertEqual(doc.toPlainText(),'Texto terminado.')
        rendered=markdown_html('[archivo](file:///C:/secret.txt) ![foto](file:///C:/secret.png) <img src="file:///C:/secret.png">')
        self.assertNotIn('<img',rendered);self.assertNotIn('href="file:',rendered)
        with patch('victor.gui.chat_text.QDesktopServices.openUrl') as open_url:
            w.open_link('file:///C:/secret.txt');w.open_link('javascript:alert(1)');open_url.assert_not_called()
            w.open_link('https://example.com');open_url.assert_called_once()
    def test_gui_chat_voice_and_narrow_theme_layout(self):
        from victor.gui.app import GUIManager
        def pump(seconds=.1):
            until=time.monotonic()+seconds
            while time.monotonic()<until:self.qt.processEvents();time.sleep(.005)
        def assert_text_fits(bubble):
            # Qt queues layout updates after a resize/font change; assert the settled layout.
            until=time.monotonic()+2
            while bubble.label.height()+2<bubble.label.heightForWidth(bubble.label.width()) and time.monotonic()<until:pump(.02)
            self.assertGreaterEqual(bubble.label.height()+2,bubble.label.heightForWidth(bubble.label.width()))
        with tempfile.TemporaryDirectory() as folder,patch('victor.gui.spotify_embed.SpotifyEmbed.start'):
            app=GUIManager(ConfigManager(Path(folder)))
            try:
                app.show();app.navigate('home');app.resize(1200,900)
                app.append_message('user','Compara las opciones y resume lo importante.')
                bubble=app.append_message('assistant',ANSWER);pump(.3)
                self.assertIsInstance(bubble.label,MarkdownLabel)
                assert_text_fits(bubble)
                app.voice_panel.response.setText(ANSWER);self.assertIsInstance(app.voice_panel.response,MarkdownLabel)
                previews=os.getenv('VICTOR_CHAT_PREVIEWS')
                if previews:
                    directory=Path(previews);directory.mkdir(parents=True,exist_ok=True);app.scroll_bottom();pump(.1);app.grab().save(str(directory/'chat-dark.png'))
                app.resize(560,900);pump(.3)
                assert_text_fits(bubble)
                if previews:app.scroll_bottom();pump(.1);app.grab().save(str(directory/'chat-narrow.png'))
                app.config.save({'theme':'Light'});app.refresh_config();app.resize(1200,900);pump(.3)
                self.assertIn('#20242F',QLabel.text(bubble.label))
                if previews:app.grab().save(str(directory/'chat-light.png'))
            finally:
                app.close();until=time.monotonic()+8
                while not app.closed_cleanly and time.monotonic()<until:pump()
            self.assertTrue(app.closed_cleanly)


def track(name,identifier,artist='Fuerza Regida',**extra):
    return dict(id=identifier,name=name,uri='spotify:track:'+identifier,type='track',artists=[{'name':artist}],album={'images':[]},**extra)


class ArtistRequests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.manager=SpotifyManager(ConfigManager(Path(self.folder.name)));self.client=Mock()
        self.manager.client=Mock(return_value=self.client);self.manager.browser=Mock(active=True,device_id='embedded')
        self.client.current_user.return_value={'product':'premium'}
    def test_any_song_routes_to_artist_filters_availability_and_avoids_repeat(self):
        from victor.gui.spotify_commands import spotify_command
        request=spotify_command('reproduce cualquier canción de fuerza regida')
        self.assertEqual(request,('spotify_play',{'query':'cualquier canción de fuerza regida'}))
        self.assertEqual(spotify_command('pon algo de Fuerza Regida'),('spotify_play',{'query':'algo de Fuerza Regida'}))
        self.assertEqual(spotify_command('pon la canción GAMINA de Kris R'),('spotify_play',{'query':'GAMINA de Kris R'}))
        self.assertIsNone(spotify_command('pon el volumen en 30'))
        self.client.search.return_value={'tracks':{'items':[track('Otro','C'*22,'Otro artista'),track('No disponible','D'*22,is_playable=False),track('Primera','A'*22),track('Segunda','B'*22)]}}
        results=[self.manager.play(request[1]['query']),self.manager.play('música de Fuerza Regida')]
        self.assertEqual({result['seleccion']['id'] for result in results},{'A'*22,'B'*22})
        self.assertTrue(all(result['seleccion']['subtitle']=='Fuerza Regida' for result in results))
        self.assertTrue(all(call.kwargs['q'].lower()=='artist:"fuerza regida"' for call in self.client.search.call_args_list))
        self.assertEqual(self.client.start_playback.call_count,2)
    def test_unknown_artist_and_missing_artist_never_play(self):
        self.client.search.return_value={'tracks':{'items':[track('Parecido','A'*22,'Fuerza Regida DJ')]}}
        with self.assertRaisesRegex(VictorError,'artista'):self.manager.play('una canción de Fuerza Regida')
        self.client.start_playback.assert_not_called()
        self.client.search.reset_mock()
        with self.assertRaisesRegex(VictorError,'artista'):self.manager.play('cualquier canción')
        self.client.search.assert_not_called()
    def test_natural_variants_and_exact_titles_remain_distinct(self):
        self.client.search.return_value={'tracks':{'items':[track('Canción','A'*22)]}}
        for query in ('algo de Fuerza Regida','alguna cancion de Fuerza Regida','una canción del grupo Fuerza Regida'):
            self.manager.play(query);self.assertTrue(self.client.search.call_args.kwargs['q'].startswith('artist:'))
        self.client.search.return_value={'tracks':{'items':[track('Cualquier canción','B'*22)]}}
        self.manager.play('Cualquier canción de Fuerza Regida')
        self.assertIn('artist:',self.client.search.call_args.kwargs['q'])
        self.manager.play('"Cualquier canción" de Fuerza Regida')
        self.assertEqual(self.client.search.call_args.kwargs['q'],'"Cualquier canción" de Fuerza Regida')
        self.client.search.return_value={'tracks':{'items':[track('Canción','A'*22)]}}
        self.manager.play('Canción de Fuerza Regida')
        self.assertEqual(self.client.search.call_args.kwargs['q'],'Canción de Fuerza Regida')


if __name__=='__main__':unittest.main()

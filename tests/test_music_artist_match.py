"""Títulos con colaboradores y artista como guía; sin cuenta ni reproducción real."""
from tests.test_music_background import ApproximateMusic
from tests.test_spotify_embed import track
from victor.errors import VictorError
from victor.integrations.music_match import exact_match, nearest_match, title_variants


class ArtistMatch(ApproximateMusic):
    def bastardo(self):
        row=track('Bastardo (feat. Ñengo Flow & Jere Klein)',artist='Pablo Chill-E')
        row['artists'] += [{'name':'Ñengo Flow'},{'name':'Jere Klein'}]
        return row

    def test_reported_bastardo_chil_e_matches_featured_title(self):
        row=self.bastardo()
        self.client.search.return_value=self.results(track('Bastardo','B'*22,artist='Otro',popularity=100),row)
        result=self.manager.play('Bastardo de Pablo Chil-E')
        self.assertEqual(result['seleccion']['id'],row['id'])
        self.assertEqual(result['coincidencia']['tipo'],'aproximada')
        self.client.start_playback.assert_called_once_with(device_id='embedded',uris=[row['uri']])

    def test_featured_credit_does_not_require_saying_collaborators(self):
        row=self.bastardo()
        for query in ('Bastardo','Bastardo de Pablo Chill E','Bastardo de Ñengo Flow','Bastardo de Jere Klein'):
            with self.subTest(query=query):self.assertTrue(exact_match(query,row))
        self.client.search.return_value=self.results(row)
        result=self.manager.play('Bastardo de Pablo Chill-E')
        self.assertNotIn('coincidencia',result);self.assertEqual(self.client.search.call_count,1)

    def test_artist_guides_last_catalog_retry_with_misspelled_title(self):
        row=self.bastardo()
        self.client.search.side_effect=[self.results(),self.results(),self.results(),self.results(row)]
        result=self.manager.play('Bastard de Pablo Chil E')
        self.assertEqual(result['seleccion']['id'],row['id'])
        self.assertEqual(self.client.search.call_args.kwargs['q'],'Bastard Pablo Chil E')
        self.assertEqual(self.client.search.call_count,4)

    def test_artist_does_not_override_a_different_title(self):
        self.client.search.return_value=self.results(track('Otra canción',artist='Pablo Chill-E'))
        with self.assertRaises(VictorError):self.manager.play('Bastardo de Pablo Chill-E')
        self.client.start_playback.assert_not_called()

    def test_every_credit_format_but_not_version_labels(self):
        for name in ('Bastardo (feat. Jere Klein)','Bastardo [ft. Jere Klein]',
                     'Bastardo - featuring Jere Klein','Bastardo feat. Jere Klein'):
            self.assertTrue(exact_match('Bastardo de Pablo Chill-E',track(name,artist='Pablo Chill-E')))
        for name in ('Bastardo Remix','Bastardo (Live)','Bastardo - Acoustic','Bastardo (Remastered)'):
            self.assertEqual(title_variants(name),(name,))
            self.assertFalse(exact_match('Bastardo',track(name)))

    def test_title_with_de_and_artist_uses_last_separator(self):
        row=track('Después de la Playa (feat. Invitado)',artist='Bad Bunny')
        self.assertTrue(exact_match('Despues de la Playa de Bad Bunny',row))
        self.assertIsNotNone(nearest_match('Despues de la Play de Bad Bunny',[row]))

    def test_featured_exact_title_beats_related_hit_and_unavailable_track(self):
        row=self.bastardo()
        unavailable=self.bastardo();unavailable.update(id='C'*22,is_playable=False,popularity=100)
        self.client.search.return_value=self.results(track('Bastardos','B'*22,artist='Pablo Chill-E',popularity=100),unavailable,row)
        self.assertEqual(self.manager.play('Bastardo de Pablo Chill-E')['seleccion']['id'],row['id'])

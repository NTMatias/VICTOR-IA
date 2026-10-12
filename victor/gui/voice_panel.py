"""Sesión de voz Grafito: comparte micrófono, contexto y permisos con el chat."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QWidget
from victor.gui.panels import Page,Columns,card,label,button
from victor.gui.widgets import icon, AudioOrb, ListeningWave, ResponsiveButtons
from victor.gui.theme import state_style

class VoicePanel(Page):
    def __init__(self,app):
        super().__init__('Asistente de voz','Habla con VICTOR sin interrumpir lo que estás haciendo.','Voz / sesión',
            (button('Volver al chat',lambda:app.show_voice(False),'file'),))
        self.app=app
        left,ll=card('Sesión de voz');ll.setSpacing(8);self.state=label('● Listo','badge');ll.addWidget(self.state,alignment=Qt.AlignmentFlag.AlignRight)
        ll.addStretch()
        self.mic=AudioOrb()
        self.mic.setToolTip('Pulsa para escuchar; en push-to-talk mantén pulsado.')
        self.mic.clicked.connect(app.toggle_mic);self.mic.pressed.connect(app.mic_press);self.mic.released.connect(app.mic_release)
        ll.addWidget(self.mic,alignment=Qt.AlignmentFlag.AlignCenter)
        self.output_meter=label('Voz de VICTOR · esperando audio');self.output_meter.setAlignment(Qt.AlignmentFlag.AlignCenter);ll.addWidget(self.output_meter)
        self.prompt=label('Pulsa el micrófono para hablar.');self.prompt.setAlignment(Qt.AlignmentFlag.AlignCenter);ll.addWidget(self.prompt)
        self.input_wave=ListeningWave();self.input_label=label('Micrófono · en espera');ll.addWidget(self.input_wave);ll.addWidget(self.input_label)
        ll.addStretch();ll.addWidget(ResponsiveButtons([button('Silenciar micrófono',app.pause_mic,'mic'),button('Finalizar escucha',app.stop,'stop',danger=True)],columns=2,cell_width=180))
        self.output_enabled=button('Voz de VICTOR',self.toggle_output,'volume');self.output_enabled.setCheckable(True);ll.addWidget(self.output_enabled)
        ll.addWidget(label('También puedes mantener pulsado para hablar.'))
        right=QWidget();rl=QVBoxLayout(right);rl.setContentsMargins(0,0,0,0);rl.setSpacing(12)
        transcript,tl=card('Transcripción de la última intervención')
        self.transcript=label('Pulsa el micrófono y habla.')
        from victor.gui.chat_text import MarkdownLabel
        self.response=MarkdownLabel('Tu respuesta aparecerá aquí.')
        tl.addWidget(label('TÚ','caption'));tl.addWidget(self.transcript)
        self.response_caption=label('VICTOR','caption');tl.addWidget(self.response_caption);tl.addWidget(self.response)
        from victor.gui.spotify_embed import SpotifyNowPlaying
        self.music=SpotifyNowPlaying();self.music.hide();tl.addWidget(self.music);tl.addStretch()
        self.confirm_button=button('Responder a la confirmación',app.listen_approval,'mic');self.confirm_button.hide();tl.addWidget(self.confirm_button);rl.addWidget(transcript,1)
        mode,ml=card('Modo de escucha');self.modes={}
        from PySide6.QtWidgets import QButtonGroup
        self.mode_group=QButtonGroup(self);self.mode_group.setExclusive(True)
        for value,title in [('manual','Manual'),('push-to-talk','Push-to-talk'),('continua','Continua')]:
            b=button(title,lambda checked=False,v=value:self.set_mode(v));b.setCheckable(True);b.setChecked(app.config.get('voice_mode')==value);self.modes[value]=b;self.mode_group.addButton(b)
        ml.addWidget(ResponsiveButtons(self.modes.values(),columns=3,cell_width=115))
        self.recognizer=label('');ml.addWidget(self.recognizer)
        self.audio_processing=label('Ruido y eco · en espera');ml.addWidget(self.audio_processing)
        ml.addWidget(button('Probar micrófono sin ejecutar órdenes',app.test_microphone,'mic'))
        ml.addWidget(button('Configurar voz y modelo',lambda:app.navigate('voice_settings'),'settings'));rl.addWidget(mode)
        columns=Columns(left,right,weights=[6,5]);columns.setMinimumHeight(550);self.content.addWidget(columns,1)
        self.sync_settings()
    def show_music(self,state):
        self.response.hide();self.response_caption.hide();self.music.update_state(state);self.music.show()
    def show_response(self):
        self.music.hide();self.response.show();self.response_caption.show()
    def sync_settings(self):
        from victor.gui.theme import is_light
        self.response.apply_theme(is_light(self.app.config.get('theme')))
        backend=self.app.config.get('voice_backend')
        name={'google':'Google','whisper':'Whisper local','openai':'OpenAI'}.get(backend,backend)
        self.recognizer.setText('Reconocimiento: '+name+(' · '+self.app.config.get('openai_transcription_model') if backend=='openai' else ''))
        for value,widget in self.modes.items():widget.setChecked(value==self.app.config.get('voice_mode'))
        self.output_enabled.setChecked(self.app.config.get('voice_enabled'))
        self.output_enabled.setText('Voz de VICTOR · activada' if self.app.config.get('voice_enabled') else 'Voz de VICTOR · desactivada')
    def toggle_output(self,checked):
        self.app.config.save({'voice_enabled':checked});self.app.settings.fields['voice_enabled'].setChecked(checked)
        if not checked:self.app.voice_output.stop();self.set_output_level(0.)
        self.sync_settings()
    def set_input_level(self,level):
        self.input_wave.set_level(level);self.input_label.setText('Micrófono · '+str(round(level*100))+' % de nivel' if level else 'Micrófono · en espera')
    def set_output_level(self,level):self.mic.set_level(level)
    def set_mode(self,mode):
        self.app.voice_input.stop();self.app.config.save({'voice_mode':mode})
        self.app.settings.fields['voice_mode'].setCurrentText(mode)
        for value,w in self.modes.items():w.setChecked(value==mode)
        if mode=='continua':self.app.queue_continuous_listening()
    def set_state(self,state):
        self.state.setText('● '+state);self.state.setStyleSheet(state_style(state))
        continuous = self.app.config.get('voice_mode') == 'continua'
        import time
        armed = time.monotonic() < self.app.voice_input.conversation_until
        listening = 'Escuchando tu petición…' if armed or not continuous else 'Di «' + self.app.config.get('wake_word') + '» para hablar.'
        self.prompt.setText(listening if state=='Escuchando' else 'Procesando tu petición…' if state=='Pensando' else 'Respondiendo… Di VICTOR para interrumpir.' if state=='Respondiendo' and continuous else 'Respondiendo…' if state=='Respondiendo' else 'Activa la escucha continua para hablar sin pulsar.' if continuous else 'Pulsa el micrófono para hablar.')

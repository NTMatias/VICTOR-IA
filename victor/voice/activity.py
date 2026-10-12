"""Silero voice activity, not loudness, defines utterance boundaries."""
import numpy as np


class SpeechDetector:
    def __init__(self):
        from faster_whisper.vad import get_speech_timestamps, VadOptions
        self.timestamps=get_speech_timestamps
        self.options=VadOptions(threshold=.5,min_speech_duration_ms=32,min_silence_duration_ms=96,speech_pad_ms=0)
        self.recent=np.empty(0,dtype=np.float32)
        self.pending=0
        self.last=False

    def reset(self):
        self.recent=np.empty(0,dtype=np.float32);self.pending=0;self.last=False

    def is_voice(self, pcm):
        audio=np.asarray(pcm,dtype=np.float32)/32768.
        self.recent=np.concatenate((self.recent,audio))[-10240:]
        self.pending+=len(audio)
        if self.pending<512:return self.last
        self.pending=0
        if np.sqrt(np.mean(self.recent**2))<.0003:self.last=False;return False
        segments=self.timestamps(self.recent.copy(),self.options)
        self.last=any(segment['end']>=len(self.recent)-1536 for segment in segments)
        return self.last

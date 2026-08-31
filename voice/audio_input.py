"""Captura de áudio do microfone da STAR."""
from pathlib import Path
import os
import tempfile
import numpy as np


class AudioRecorder:
    def __init__(self, samplerate=16000, channels=1):
        self.samplerate=samplerate
        self.channels=channels
        self.stream=None
        self.frames=[]
        self.recording=False
        self.last_error=None

    @property
    def available(self):
        try:
            import sounddevice  # noqa: F401
            return True
        except Exception:
            return False

    def start(self):
        import sounddevice as sd
        if self.recording:
            return
        self.frames=[]
        self.last_error=None

        def callback(indata, frames, time_info, status):
            if status:
                self.last_error=str(status)
            self.frames.append(indata.copy())

        self.stream=sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            dtype="float32",
            callback=callback,
        )
        self.stream.start()
        self.recording=True

    def stop(self):
        stream=self.stream
        self.stream=None
        self.recording=False
        if stream is not None:
            try:
                stream.stop()
            finally:
                stream.close()

    def stop_to_wav(self):
        if not self.recording:
            return None

        try:
            self.stop()
        except Exception:
            self.stream=None
            self.recording=False
            raise

        if not self.frames:
            raise RuntimeError("Nenhum áudio foi capturado.")

        import soundfile as sf

        data=np.concatenate(self.frames, axis=0)
        fd, name=tempfile.mkstemp(prefix="star_mic_", suffix=".wav")
        os.close(fd)
        out=Path(name)
        sf.write(str(out), data, self.samplerate, subtype="PCM_16")
        return out

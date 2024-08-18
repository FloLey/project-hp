import pyaudio
import numpy as np


class AudioUtils:
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    THRESHOLD = 900
    SILENCE_LIMIT = 2
    PREV_AUDIO = 0.5

    def __init__(self):
        self.p = pyaudio.PyAudio()

    def is_silent(self, data_chunk):
        return max(np.frombuffer(data_chunk, dtype=np.int16)) < self.THRESHOLD

    def record_phrase(self, stream, prev_audio):
        frames = list(prev_audio)
        silent_chunks = 0
        while True:
            data = stream.read(self.CHUNK, exception_on_overflow=False)
            frames.append(data)
            silent = self.is_silent(data)

            if silent:
                silent_chunks += 1
                if silent_chunks > self.SILENCE_LIMIT * self.RATE / self.CHUNK:
                    break
            else:
                silent_chunks = 0

        return frames

    def get_input_stream(self):
        return self.p.open(format=self.FORMAT,
                           channels=self.CHANNELS,
                           rate=self.RATE,
                           input=True,
                           frames_per_buffer=self.CHUNK)

    def get_output_stream(self):
        return self.p.open(format=pyaudio.paInt16,
                           channels=1,
                           rate=24000,
                           output=True)

    def terminate(self):
        self.p.terminate()

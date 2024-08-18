import wave
import tempfile
import os
import string
from config import client


class Transcriber:
    @staticmethod
    def clean_text(text):
        return ''.join(char.lower() for char in text if char not in string.punctuation)

    @staticmethod
    def transcribe_audio(frames, audio_utils):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
            wf = wave.open(temp_wav.name, 'wb')
            wf.setnchannels(audio_utils.CHANNELS)
            wf.setsampwidth(audio_utils.p.get_sample_size(audio_utils.FORMAT))
            wf.setframerate(audio_utils.RATE)
            wf.writeframes(b''.join(frames))
            wf.close()

            with open(temp_wav.name, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="fr"
                )

        os.unlink(temp_wav.name)
        return Transcriber.clean_text(transcript.text)

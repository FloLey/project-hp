import sys
import sounddevice as sd
import pyaudio
from config import ELEVENLABS_API_KEY, ELEVENLABS_TTS_SPEED, ELEVENLABS_VOICE_ID, OPENAI_TTS_SPEED
from pydub import AudioSegment
import io
import requests
from config import client
import numpy as np
from abc import ABC, abstractmethod


class TextToSpeech(ABC):
    @abstractmethod
    def speak_and_capture_text(self, text):
        pass


class OpenAITTS(TextToSpeech):
    def speak_and_capture_text(self, text):
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=text,
            response_format="mp3",
            speed=OPENAI_TTS_SPEED
        )

        audio_data = b""
        for chunk in response.iter_bytes(1024):
            audio_data += chunk

        audio = AudioSegment.from_mp3(io.BytesIO(audio_data))
        self._play_audio(audio)

        return audio

    def _play_audio(self, audio):
        def audio_callback(outdata, frames, time, status):
            if status:
                print(status, file=sys.stderr)
            chunksize = min(len(audio_array) - audio_pos[0], frames)
            outdata[:chunksize, 0] = audio_array[audio_pos[0]:audio_pos[0] + chunksize]
            if chunksize < frames:
                outdata[chunksize:, 0] = 0
                raise sd.CallbackStop()
            audio_pos[0] += chunksize

        audio_array = np.array(audio.get_array_of_samples()
                               ).astype(np.float32) / 32768.0
        audio_pos = [0]

        try:
            stream = sd.OutputStream(
                samplerate=audio.frame_rate,
                channels=1,
                callback=audio_callback,
                finished_callback=lambda: print("Audio played successfully.")
            )

            with stream:
                sd.sleep(int(len(audio_array) / audio.frame_rate * 1000))
        except Exception as e:
            print(f"Error during audio playback: {e}")


class ElevenLabsTTS(TextToSpeech):
    def __init__(self):
        self.tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{
            ELEVENLABS_VOICE_ID}/stream"
        self.headers = {
            "Accept": "audio/mpeg",
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }

    def speak_and_capture_text(self, text):
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.8,
                "similarity_boost": 0.3,
                "style": 0.1,
                "use_speaker_boost": True
            }
        }

        response = requests.post(
            self.tts_url, json=data, headers=self.headers, stream=True)

        if response.ok:
            buffer = io.BytesIO()
            for chunk in response.iter_content(chunk_size=4096):
                if chunk:
                    buffer.write(chunk)

            buffer.seek(0)
            complete_audio = AudioSegment.from_mp3(buffer)
            faster_audio = complete_audio.speedup(
                playback_speed=ELEVENLABS_TTS_SPEED)

            self._play_audio(faster_audio)

            return faster_audio
        else:
            print(f"Error in text-to-speech: {response.text}")
            return None

    def _play_audio(self, audio):
        def audio_callback(outdata, frames, time, status):
            if status:
                print(status, file=sys.stderr)
            chunksize = min(len(audio_array) - audio_pos[0], frames)
            outdata[:chunksize, 0] = audio_array[audio_pos[0]:audio_pos[0] + chunksize]
            if chunksize < frames:
                outdata[chunksize:, 0] = 0
                raise sd.CallbackStop()
            audio_pos[0] += chunksize

        audio_array = np.array(audio.get_array_of_samples()
                               ).astype(np.float32) / 32768.0
        audio_pos = [0]

        try:
            stream = sd.OutputStream(
                samplerate=audio.frame_rate,
                channels=1,
                callback=audio_callback,
                finished_callback=lambda: print("Audio played successfully.")
            )

            with stream:
                sd.sleep(int(len(audio_array) / audio.frame_rate * 1000))
        except Exception as e:
            print(f"Error during audio playback: {e}")

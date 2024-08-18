import os
from datetime import datetime
from collections import deque
from audio_utils import AudioUtils
from transcription import Transcriber
from gpt_interface import GPTInterface
from text_to_speech import OpenAITTS, ElevenLabsTTS
from email_sender import EmailSender
from config import START_WORD, STOP_WORD, GMAIL_CREDENTIALS_FILE
from pydub import AudioSegment
import numpy as np


class SortingHat:
    def __init__(self, tts_service='openai'):
        self.audio_utils = AudioUtils()
        self.transcriber = Transcriber()
        self.gpt_interface = GPTInterface()
        if tts_service == 'openai':
            self.tts = OpenAITTS()
        elif tts_service == 'elevenlabs':
            self.tts = ElevenLabsTTS()
        else:
            raise ValueError(
                "Invalid TTS service. Choose 'openai' or 'elevenlabs'.")
        self.email_sender = EmailSender()
        self.conversation_audio = AudioSegment.empty()
        self.conversation_dir = r"C:\Users\flore\OneDrive\Desktop\project-hp\conversations"
        os.makedirs(self.conversation_dir, exist_ok=True)

    def listen_and_process(self):
        input_stream = self.audio_utils.get_input_stream()
        print(f"En attente du mot '{START_WORD}' pour commencer...")

        prev_audio = deque(maxlen=int(
            self.audio_utils.PREV_AUDIO * self.audio_utils.RATE / self.audio_utils.CHUNK))

        try:
            while True:
                if self._listen_for_start_word(input_stream, prev_audio):
                    self._converse_with_gpt(input_stream, prev_audio)
        except KeyboardInterrupt:
            print("Interruption manuelle. Arrêt du programme.")
        finally:
            input_stream.stop_stream()
            input_stream.close()

    def _listen_for_start_word(self, input_stream, prev_audio):
        while True:
            data = input_stream.read(
                self.audio_utils.CHUNK, exception_on_overflow=False)
            prev_audio.append(data)
            if not self.audio_utils.is_silent(data):
                frames = self.audio_utils.record_phrase(
                    input_stream, prev_audio)
                text = self.transcriber.transcribe_audio(
                    frames, self.audio_utils)
                print(f"Entendu: {text}")

                if self.transcriber.clean_text(START_WORD) in text:
                    print("Mot de démarrage détecté ! Entrant en mode conversation...")
                    return True

    def _converse_with_gpt(self, input_stream, prev_audio):
        conversation_history = []

        initial_greeting = self.gpt_interface.get_gpt_response(
            "Salut, je suis prêt pour la répartition.", conversation_history)
        print(f"Réponse Chapeau magique: {initial_greeting}")
        greeting_audio = self.tts.speak_and_capture_text(
            initial_greeting)
        self._add_to_conversation_audio(greeting_audio, is_user=False)

        while True:
            data = input_stream.read(
                self.audio_utils.CHUNK, exception_on_overflow=False)
            prev_audio.append(data)
            if not self.audio_utils.is_silent(data):
                frames = self.audio_utils.record_phrase(
                    input_stream, prev_audio)
                text = self.transcriber.transcribe_audio(
                    frames, self.audio_utils)
                print(f"Vous avez dit: {text}")
                self._add_to_conversation_audio(frames, is_user=True)

                if self.transcriber.clean_text(STOP_WORD) in text:
                    print(
                        "Mot d'arrêt détecté. Envoi de l'e-mail et retour au mode d'écoute initial.")
                    audio_file_path = self._save_conversation_audio()
                    self.email_sender.send_conversation_email(
                        conversation_history, "florent.lejoly@gmail.com", audio_file_path)
                    break

                gpt_response = self.gpt_interface.get_gpt_response(
                    text, conversation_history)
                print(f"Réponse Chapeau magique: {gpt_response}")
                response_audio = self.tts.speak_and_capture_text(
                    gpt_response)
                self._add_to_conversation_audio(response_audio, is_user=False)

    def _add_to_conversation_audio(self, content, is_user):
        if is_user:
            audio = AudioSegment(
                data=b''.join(content),
                sample_width=self.audio_utils.p.get_sample_size(
                    self.audio_utils.FORMAT),
                frame_rate=self.audio_utils.RATE,
                channels=self.audio_utils.CHANNELS
            )
        else:
            if isinstance(content, AudioSegment):
                audio = content
            else:
                raise ValueError("Type d'audio non reconnu")

        if audio:
            silence = AudioSegment.silent(duration=1000)
            self.conversation_audio += silence + audio

    def _save_conversation_audio(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(
            self.conversation_dir, f"conversation_choixpeau_{timestamp}.mp3")
        self.conversation_audio.export(output_file, format="mp3")
        print(f"Conversation audio saved to {output_file}")
        return output_file

    def run(self):
        print(f"Dites '{START_WORD}' pour commencer la conversation avec GPT.")
        print(f"Dites '{
              STOP_WORD}' pour arrêter la conversation et revenir au mode d'écoute initial.")
        print("Appuyez sur Ctrl+C pour quitter le programme.")

        try:
            self.listen_and_process()
        except KeyboardInterrupt:
            print("Fermeture du programme.")
        finally:
            self.audio_utils.terminate()

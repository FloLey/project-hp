from email_sender import EmailSender
import os
import wave
import struct


def create_test_audio():
    # Créer un fichier WAV de test
    duration = 3  # secondes
    frequency = 440  # Hz
    sample_rate = 44100
    num_samples = duration * sample_rate

    with wave.open("test_audio.wav", "w") as wav_file:
        wav_file.setnchannels(1)  # mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        for i in range(num_samples):
            value = int(32767.0 * ((i * frequency) / sample_rate) % 1)
            data = struct.pack('<h', value)
            wav_file.writeframesraw(data)

    # Convertir WAV en MP3 (nécessite ffmpeg)
    os.system("ffmpeg -i test_audio.wav -acodec libmp3lame -b:a 128k test_audio.mp3")
    os.remove("test_audio.wav")


def test_email_sending():
    email_sender = EmailSender()

    conversation_history = [
        {"role": "assistant", "content": "Bonjour ! Je suis le Choixpeau Magique."},
        {"role": "user", "content": "Salut ! Je m'appelle Harry."},
        {"role": "assistant", "content": "Enchanté, Harry ! Prêt à être réparti ?"},
        {"role": "user", "content": "Oui, je suis prêt !"},
        {"role": "assistant", "content": "Hmm, je vois du courage... de l'intelligence aussi. Tu serais parfait pour... GRYFFONDOR !"}
    ]

    create_test_audio()
    test_audio_path = "test_audio.mp3"

    # Remplacez par votre email de test
    recipient_email = "votre_email_test@example.com"
    try:
        email_sender.send_conversation_email(
            conversation_history, recipient_email, test_audio_path)
    except Exception as e:
        print(f"Erreur lors du test d'envoi d'e-mail : {e}")

    os.remove(test_audio_path)


if __name__ == "__main__":
    test_email_sending()

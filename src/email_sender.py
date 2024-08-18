import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.audio import MIMEAudio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
from config import GMAIL_CREDENTIALS_FILE, EMAIL_SENDER

SCOPES = ['https://www.googleapis.com/auth/gmail.send']


class EmailSender:
    def __init__(self):
        self.creds = None
        self.token_file = 'token.pickle'

        # Charger les credentials existants
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                self.creds = pickle.load(token)

        # Si les credentials n'existent pas ou ne sont plus valides, en créer de nouveaux
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    GMAIL_CREDENTIALS_FILE, SCOPES)
                self.creds = flow.run_local_server(port=0)

            # Sauvegarder les credentials pour la prochaine exécution
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('gmail', 'v1', credentials=self.creds)

    def send_conversation_email(self, conversation_history, recipient_email, audio_file_path):
        message = MIMEMultipart()
        message['To'] = recipient_email
        message['From'] = EMAIL_SENDER
        message['Subject'] = 'Conversation avec le Choixpeau Magique'

        body = "Voici la transcription de la conversation avec le Choixpeau Magique :\n\n"
        for msg in conversation_history:
            role = "Choixpeau" if msg["role"] == "assistant" else "Utilisateur"
            body += f"{role}: {msg['content']}\n\n"

        message.attach(MIMEText(body))

        with open(audio_file_path, 'rb') as audio_file:
            audio_data = audio_file.read()
        audio = MIMEAudio(audio_data, _subtype="mpeg")
        audio.add_header('Content-Disposition', 'attachment',
                         filename=os.path.basename(audio_file_path))
        message.attach(audio)

        raw_message = base64.urlsafe_b64encode(
            message.as_bytes()).decode('utf-8')
        try:
            send_message = self.service.users().messages().send(
                userId="me", body={'raw': raw_message}).execute()
            print(
                f"E-mail envoyé avec succès. Message Id: {send_message['id']}")
        except Exception as error:
            print(f"Une erreur est survenue : {error}")

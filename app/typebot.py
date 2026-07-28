"""
Cliente para comunicarse con Typebot.

Este módulo inicia conversaciones y envía mensajes
utilizando la API oficial de Typebot.
"""

import requests

from app.config import (
    TYPEBOT_API_TOKEN,
    TYPEBOT_PUBLIC_ID,
)

# ----------------------------------------------------------
# Sesiones temporales (Versión 1)
# ----------------------------------------------------------

# WhatsApp -> sessionId
sessions = {}


class TypebotClient:
    BASE_URL = "https://typebot.io/api/v1"

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {TYPEBOT_API_TOKEN}",
            "Content-Type": "application/json",
        }

    def get_session(self, phone_number):
        return sessions.get(phone_number)

    def save_session(self, phone_number, session_id):
        sessions[phone_number] = session_id

    def start_chat(self, phone_number):

        url = f"{self.BASE_URL}/typebots/{TYPEBOT_PUBLIC_ID}/startChat"

        response = requests.post(
            url,
            headers=self.headers,
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()

        session_id = data["sessionId"]

        self.save_session(phone_number, session_id)

        return session_id

    def continue_chat(self, session_id, message):

        url = f"{self.BASE_URL}/sessions/{session_id}/continueChat"

        payload = {
            "message": message
        }

        response = requests.post(
            url,
            json=payload,
            headers=self.headers,
            timeout=20,
        )

        response.raise_for_status()

        return response.json()

    def send_message(self, phone_number, message):

        session = self.get_session(phone_number)

        if session is None:
            session = self.start_chat(phone_number)

        return self.continue_chat(session, message)
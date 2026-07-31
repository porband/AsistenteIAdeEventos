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
# NOTA: esto vive en memoria. Si Railway reinicia o redespliega
# el servidor, este diccionario se borra y todos los usuarios
# arrancan una sesión nueva automáticamente (no rompe nada,
# solo "olvida" en qué paso del flujo iba cada quien).

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

    def clear_session(self, phone_number):
        sessions.pop(phone_number, None)

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

        # Devolvemos la respuesta COMPLETA (no solo el id), porque ya
        # trae el mensaje de bienvenida y el primer bloque de entrada
        # (por ejemplo, el menú). Esto tiene la misma forma que la
        # respuesta de continue_chat: {"messages": [...], "input": {...}}
        return data

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

        # Caso 1: no hay sesión guardada -> es un chat nuevo.
        # El "Hola" (o lo que sea que haya escrito el usuario) es solo
        # el disparador para arrancar la conversación; NO se reenvía
        # como respuesta a nada, porque el propio startChat ya trae
        # el mensaje de bienvenida y el primer bloque de entrada.
        if session is None:
            return self.start_chat(phone_number)

        # Caso 2: ya había sesión -> intentar continuar la conversación
        try:
            return self.continue_chat(session, message)

        except requests.exceptions.HTTPError as error:
            respuesta_http = error.response

            # La sesión expiró o ya no existe en Typebot (404):
            # descartamos la sesión vieja y arrancamos una conversación
            # nueva desde cero (igual que el Caso 1).
            if respuesta_http is not None and respuesta_http.status_code == 404:
                print(
                    f"\nSesión de Typebot expirada para {phone_number}. "
                    "Reiniciando conversación desde cero..."
                )
                self.clear_session(phone_number)
                return self.start_chat(phone_number)

            # Cualquier otro error HTTP (500, 401, etc.) se propaga,
            # para no ocultar problemas reales de configuración.
            raise

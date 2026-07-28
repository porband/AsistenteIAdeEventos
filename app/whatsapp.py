"""
Funciones para enviar mensajes utilizando
la API de WhatsApp Cloud (Meta).
"""

import requests

from app.config import (
    WHATSAPP_TOKEN,
    PHONE_NUMBER_ID,
)


def enviar_mensaje(numero: str, mensaje: str):

    url = (
        f"https://graph.facebook.com/v23.0/"
        f"{PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {
            "body": mensaje
        }
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=20
    )

    print("====================================")
    print("RESPUESTA DE META")
    print(response.status_code)
    print(response.text)
    print("====================================")

    response.raise_for_status()

    return response.json()
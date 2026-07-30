"""
Funciones para enviar mensajes utilizando
la API de WhatsApp Cloud (Meta).
"""

import requests

from app.config import (
    WHATSAPP_TOKEN,
    PHONE_NUMBER_ID,
)


def _url_mensajes():
    return f"https://graph.facebook.com/v23.0/{PHONE_NUMBER_ID}/messages"


def _headers():
    return {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }


def _post(payload: dict):
    response = requests.post(
        _url_mensajes(),
        headers=_headers(),
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


def enviar_mensaje(numero: str, mensaje: str):
    """Manda un mensaje de texto plano."""

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {
            "body": mensaje
        }
    }

    return _post(payload)


def enviar_botones(numero: str, texto: str, opciones: list[dict]):
    """
    Manda hasta 3 botones de respuesta rápida (WhatsApp Reply Buttons).

    opciones: lista de dicts con "id" y "title", ej:
        [{"id": "abc123", "title": "Confirmar asistencia"}, ...]

    Nota: WhatsApp exige título de máx. 20 caracteres por botón.
    """

    botones = []
    for opcion in opciones[:3]:
        titulo = (opcion.get("title") or "Opción").strip()
        if len(titulo) > 20:
            titulo = titulo[:19] + "…"

        botones.append({
            "type": "reply",
            "reply": {
                "id": str(opcion.get("id") or titulo),
                "title": titulo,
            }
        })

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": texto or "Elige una opción:"
            },
            "action": {
                "buttons": botones
            }
        }
    }

    return _post(payload)


def enviar_lista(numero: str, texto: str, opciones: list[dict], titulo_boton: str = "Ver opciones"):
    """
    Manda un menú tipo lista desplegable (para más de 3 opciones).

    opciones: lista de dicts con "id" y "title".
    """

    filas = []
    for opcion in opciones[:10]:  # Meta permite hasta 10 filas por lista
        titulo = (opcion.get("title") or "Opción").strip()
        if len(titulo) > 24:
            titulo = titulo[:23] + "…"

        filas.append({
            "id": str(opcion.get("id") or titulo),
            "title": titulo,
        })

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {
                "text": texto or "Elige una opción:"
            },
            "action": {
                "button": titulo_boton[:20],
                "sections": [
                    {
                        "title": "Opciones",
                        "rows": filas
                    }
                ]
            }
        }
    }

    return _post(payload)
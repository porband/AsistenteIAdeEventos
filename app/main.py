from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import json

from app.config import VERIFY_TOKEN
from app.typebot import TypebotClient
from app.whatsapp import enviar_mensaje, enviar_botones, enviar_lista

app = FastAPI(
    title="Asistente IA de Eventos",
    version="1.0.0"
)

typebot = TypebotClient()


@app.get("/")
def inicio():
    return {
        "mensaje": "Servidor funcionando correctamente"
    }


@app.get("/salud")
def salud():
    return {
        "estado": "OK"
    }


# -------------------------------------------------
# VERIFICACIÓN DEL WEBHOOK
# -------------------------------------------------

@app.get("/webhook")
async def verificar_webhook(request: Request):

    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if (
        mode == "subscribe"
        and token == VERIFY_TOKEN
        and challenge is not None
    ):
        return PlainTextResponse(challenge)

    return PlainTextResponse("Forbidden", status_code=403)


# -------------------------------------------------
# UTILIDAD: extraer texto plano de la respuesta de Typebot
# -------------------------------------------------

def extraer_texto_typebot(respuesta: dict) -> str | None:
    """
    Typebot puede devolver el contenido de un mensaje como:
      - string plano
      - dict tipo richText: {"type": "richText", "richText": [...]}
    Esta función devuelve siempre un string plano, o None si no
    encontró texto utilizable.
    """
    if not isinstance(respuesta, dict):
        return None

    for item in respuesta.get("messages", []):
        contenido = item.get("content")

        # Caso 1: ya viene como texto plano
        if isinstance(contenido, str) and contenido.strip():
            return contenido.strip()

        # Caso 2: viene como richText
        if isinstance(contenido, dict) and contenido.get("type") == "richText":
            partes = []
            for bloque in contenido.get("richText", []):
                linea = "".join(
                    hijo.get("text", "")
                    for hijo in bloque.get("children", [])
                    if "text" in hijo
                )
                if linea:
                    partes.append(linea)
            texto = "\n".join(partes).strip()
            if texto:
                return texto

    return None


# -------------------------------------------------
# RECEPCIÓN DE MENSAJES
# -------------------------------------------------

@app.post("/webhook")
async def recibir_webhook(request: Request):

    data = await request.json()

    print("\n==========================")
    print("MENSAJE RECIBIDO")
    print("==========================")
    print(json.dumps(data, indent=4, ensure_ascii=False))

    try:
        entry_list = data.get("entry") or []
        if not entry_list:
            return PlainTextResponse("EVENT_RECEIVED", status_code=200)

        changes_list = entry_list[0].get("changes") or []
        if not changes_list:
            return PlainTextResponse("EVENT_RECEIVED", status_code=200)

        value = changes_list[0].get("value") or {}

        if "messages" not in value or not value["messages"]:
            # Puede ser un evento de "status" (entregado/leído), no un mensaje nuevo
            return PlainTextResponse("EVENT_RECEIVED", status_code=200)

        mensaje = value["messages"][0]
        telefono = mensaje["from"]
        tipo_mensaje = mensaje.get("type")

        if tipo_mensaje == "text":
            texto = mensaje["text"]["body"]

        elif tipo_mensaje == "interactive":
            interactive = mensaje.get("interactive", {})
            sub_tipo = interactive.get("type")

            if sub_tipo == "button_reply":
                texto = interactive["button_reply"]["title"]
            elif sub_tipo == "list_reply":
                texto = interactive["list_reply"]["title"]
            else:
                print(f"Tipo interactive no manejado: {sub_tipo}")
                return PlainTextResponse("EVENT_RECEIVED", status_code=200)

        else:
            print(f"Mensaje tipo '{tipo_mensaje}' no manejado, se ignora.")
            return PlainTextResponse("EVENT_RECEIVED", status_code=200)

        print(f"\nUsuario: {telefono}")
        print(f"Mensaje: {texto}")

        print("\nEnviando a Typebot...")

        respuesta = typebot.send_message(telefono, texto)

        print("\nRespuesta Typebot:")
        print(json.dumps(respuesta, indent=4, ensure_ascii=False))

        texto_respuesta = extraer_texto_typebot(respuesta)
        input_block = respuesta.get("input") if isinstance(respuesta, dict) else None

        opciones = []
        if isinstance(input_block, dict) and input_block.get("type") == "choice input":
            for item in input_block.get("items", []):
                contenido = item.get("content")
                if contenido:
                    opciones.append({
                        "id": item.get("id"),
                        "title": contenido,
                    })

        cuerpo = texto_respuesta or "Elige una opción:"

        if opciones and len(opciones) <= 3:
            print(f"\nEnviando botones a WhatsApp: {[o['title'] for o in opciones]}")
            enviar_botones(telefono, cuerpo, opciones)

        elif opciones:
            print(f"\nEnviando lista a WhatsApp: {[o['title'] for o in opciones]}")
            enviar_lista(telefono, cuerpo, opciones)

        elif texto_respuesta:
            print(f"\nEnviando texto a WhatsApp:\n{texto_respuesta}")
            enviar_mensaje(telefono, texto_respuesta)

        else:
            print("Typebot no devolvió texto ni opciones utilizables.")

    except Exception as e:
        print("\nERROR")
        print(e)

    return PlainTextResponse("EVENT_RECEIVED", status_code=200)

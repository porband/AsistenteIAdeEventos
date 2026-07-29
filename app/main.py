from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import json

from app.config import VERIFY_TOKEN
from app.typebot import TypebotClient
from app.whatsapp import enviar_mensaje

from app.typebot import TypebotClient
from app.whatsapp import enviar_mensaje

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

        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" not in value:
            return PlainTextResponse(
                "EVENT_RECEIVED",
                status_code=200
            )

        mensaje = value["messages"][0]

        if mensaje["type"] != "text":
            return PlainTextResponse(
                "EVENT_RECEIVED",
                status_code=200
            )

        telefono = mensaje["from"]
        texto = mensaje["text"]["body"]

        print(f"\nUsuario: {telefono}")
        print(f"Mensaje: {texto}")

        print("\nEnviando a Typebot...")

        bot = TypebotClient()
        respuesta = bot.send_message(
            telefono,
            texto
        )

        print("\nRespuesta Typebot:")
        print(json.dumps(respuesta, indent=4, ensure_ascii=False))

        texto_respuesta = None

        if "messages" in respuesta:

            for item in respuesta["messages"]:

                if item.get("type") == "text":
                    texto_respuesta = item.get("content")
                    break

        if texto_respuesta:

            print(f"\nEnviando a WhatsApp:\n{texto_respuesta}")

            enviar_mensaje(
                telefono,
                texto_respuesta
            )

        else:

            print("Typebot no devolvió texto.")

    except Exception as e:

        print("\nERROR")
        print(e)

    return PlainTextResponse(
        "EVENT_RECEIVED",
        status_code=200
    )
    try:

        if "entry" not in data:
            return PlainTextResponse("EVENT_RECEIVED", status_code=200)

        entry = data["entry"][0]

        if "changes" not in entry:
            return PlainTextResponse("EVENT_RECEIVED", status_code=200)

        value = entry["changes"][0]["value"]

        if "messages" not in value:
            return PlainTextResponse("EVENT_RECEIVED", status_code=200)

        mensaje = value["messages"][0]

        numero = mensaje["from"]

        if mensaje["type"] != "text":
            print("Mensaje no es de texto.")
            return PlainTextResponse("EVENT_RECEIVED", status_code=200)

        texto = mensaje["text"]["body"]

        print(f"Usuario : {numero}")
        print(f"Mensaje : {texto}")

        respuesta = typebot.send_message(
            numero,
            texto
        )

        print("\nRESPUESTA TYPEBOT")
        print(json.dumps(respuesta, indent=4, ensure_ascii=False))

        texto_respuesta = None

        if isinstance(respuesta, dict):

            messages = respuesta.get("messages", [])

            for item in messages:

                if item.get("type") == "text":

                    contenido = item.get("content")

                    if contenido:
                        texto_respuesta = contenido
                        break

        if texto_respuesta:

            enviar_mensaje(
                numero,
                texto_respuesta
            )

            print("Respuesta enviada correctamente.")

        else:

            print("Typebot no devolvió texto.")

    except Exception as e:

        print("\nERROR")
        print(e)

    return PlainTextResponse(
        "EVENT_RECEIVED",
        status_code=200
    )
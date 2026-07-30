from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import json

from app.config import VERIFY_TOKEN
from app.typebot import TypebotClient
from app.whatsapp import enviar_mensaje, enviar_botones, enviar_lista, enviar_imagen

app = FastAPI(
    title="Asistente IA de Eventos",
    version="1.0.0"
)

typebot = TypebotClient()

# WhatsApp -> {id_boton: texto_completo_original}
# Se usa para reenviar a Typebot el texto EXACTO de la opción elegida,
# ya que WhatsApp trunca los títulos de botón a 20 caracteres.
opciones_pendientes: dict[str, dict[str, str]] = {}


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
                boton_id = interactive["button_reply"]["id"]
                titulo_truncado = interactive["button_reply"]["title"]
                texto = opciones_pendientes.get(telefono, {}).get(boton_id, titulo_truncado)
            elif sub_tipo == "list_reply":
                fila_id = interactive["list_reply"]["id"]
                titulo_truncado = interactive["list_reply"]["title"]
                texto = opciones_pendientes.get(telefono, {}).get(fila_id, titulo_truncado)
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

        if not isinstance(respuesta, dict):
            print("Respuesta de Typebot con formato inesperado.")
            return PlainTextResponse("EVENT_RECEIVED", status_code=200)

        algo_enviado = False

        # -----------------------------------------------------
        # 1) Recorrer TODOS los mensajes (imagen, texto, etc.)
        #    en el orden en que Typebot los mandó
        # -----------------------------------------------------
        for item in respuesta.get("messages", []):
            tipo_item = item.get("type")

            if tipo_item == "text":
                contenido = item.get("content")

                if isinstance(contenido, dict):
                    texto_item = extraer_texto_typebot({"messages": [item]})
                elif isinstance(contenido, str):
                    texto_item = contenido.strip()
                else:
                    texto_item = None

                if texto_item:
                    print(f"\nEnviando texto a WhatsApp:\n{texto_item}")
                    enviar_mensaje(telefono, texto_item)
                    algo_enviado = True

            elif tipo_item == "image":
                url_imagen = (item.get("content") or {}).get("url")

                if url_imagen:
                    print(f"\nEnviando imagen a WhatsApp: {url_imagen}")
                    enviar_imagen(telefono, url_imagen)
                    algo_enviado = True

            else:
                print(f"Tipo de mensaje de Typebot aún no manejado: {tipo_item}")

        # -----------------------------------------------------
        # 2) Si el siguiente paso del flujo es un choice input,
        #    mandar botones (o lista) al final
        # -----------------------------------------------------
        input_block = respuesta.get("input")
        opciones = []

        if isinstance(input_block, dict) and input_block.get("type") == "choice input":
            for item in input_block.get("items", []):
                contenido = item.get("content")

                if isinstance(contenido, dict):
                    contenido = extraer_texto_typebot({"messages": [{"content": contenido}]})

                if isinstance(contenido, str) and contenido.strip():
                    opciones.append({
                        "id": item.get("id"),
                        "title": contenido.strip(),
                    })

        if opciones:
            # Guardamos el texto COMPLETO de cada opción, indexado por
            # el id del botón, para recuperarlo exacto cuando el usuario
            # toque uno (WhatsApp nos devolvería el título truncado).
            opciones_pendientes[telefono] = {
                o["id"]: o["title"] for o in opciones if o.get("id")
            }

            cuerpo_opciones = "Elige una opción:"

            if len(opciones) <= 3:
                print(f"\nEnviando botones a WhatsApp: {[o['title'] for o in opciones]}")
                enviar_botones(telefono, cuerpo_opciones, opciones)
            else:
                print(f"\nEnviando lista a WhatsApp: {[o['title'] for o in opciones]}")
                enviar_lista(telefono, cuerpo_opciones, opciones)

            algo_enviado = True

        if not algo_enviado:
            print("Typebot no devolvió contenido enviable.")

    except Exception as e:
        print("\nERROR")
        print(e)

    return PlainTextResponse("EVENT_RECEIVED", status_code=200)

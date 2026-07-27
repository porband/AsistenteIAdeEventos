from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import json

app = FastAPI(
    title="Asistente IA de Eventos",
    version="1.0.0"
)

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


# ---------------------------
# WEBHOOK DE META
# ---------------------------

VERIFY_TOKEN = "AsistenteIAEventos2026"

@app.get("/webhook")
async def verificar_webhook(request: Request):

    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)

    return {"error": "Token incorrecto"}

@app.post("/webhook")
async def recibir_webhook(request: Request):

    data = await request.json()

    print("\n==========================")
    print("MENSAJE RECIBIDO")
    print("==========================")
    print(json.dumps(data, indent=4, ensure_ascii=False))

    return PlainTextResponse("EVENT_RECEIVED", status_code=200)
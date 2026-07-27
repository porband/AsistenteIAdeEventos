from fastapi import FastAPI, Request

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
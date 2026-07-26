from fastapi import FastAPI

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
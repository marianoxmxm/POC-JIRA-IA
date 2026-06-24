from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os

app = FastAPI()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = "llama3.2:3b"

class JiraTicket(BaseModel):
    issue_key: str
    summary: str
    description: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/analizar-ticket")
def analizar_ticket(ticket: JiraTicket):
    texto_ticket = f"Resumen: {ticket.summary}\nDescripción: {ticket.description}"
    
    prompt = f"""
    Actúa como un clasificador experto de Mesa de Ayuda de TI.
    Analiza el siguiente ticket:
    
    ---
    {texto_ticket}
    ---
    
    Responde ÚNICAMENTE con un objeto JSON válido, sin formato markdown, sin texto extra.
    Claves del JSON:
    1. "categoria": Elegir entre [Infraestructura, Redes, Aplicaciones, Seguridad, IAM, Hardware].
    2. "confianza": Valor entre 0.0 y 1.0.
    3. "informacion_insuficiente": true o false.
    4. "comentario_sugerido": Repregunta si falta info, o diagnóstico breve si está claro.

    Respuesta JSON:
    """

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.0}
            },
            timeout=180
        )
        return {
            "ticket_evaluado": ticket.issue_key,
            "analisis_ia": response.json().get("response", "").strip()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
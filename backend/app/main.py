"""Point d'entrée FastAPI de DevOnboard Copilot."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import chat, health, ingest

app = FastAPI(
    title="DevOnboard Copilot",
    description="Copilote IA d'onboarding développeur : indexe un repo Git et répond en citant ses sources.",
    version="1.0.0",
)

# CORS ouvert (démo hackathon) — à restreindre en production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(ingest.router, tags=["ingest"])
app.include_router(chat.router, tags=["chat"])


@app.get("/")
def root():
    return {"service": "DevOnboard Copilot", "docs": "/docs"}

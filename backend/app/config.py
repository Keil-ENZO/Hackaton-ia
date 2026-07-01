"""Chargement de la configuration depuis l'environnement (.env)."""
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_store")

    # Nom de la collection ChromaDB
    COLLECTION_NAME: str = "devonboard"

    # Nombre de chunks récupérés lors d'une recherche
    # 12 permet de couvrir à la fois du code ET des fichiers config/README
    TOP_K: int = 12

    # Taille max d'un fichier indexé (en octets) — 500 Ko
    MAX_FILE_SIZE: int = 500 * 1024


settings = Settings()

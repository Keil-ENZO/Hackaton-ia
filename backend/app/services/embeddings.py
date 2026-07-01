"""Génération d'embeddings via onnxruntime (all-MiniLM-L6-v2).

On utilise la fonction d'embedding par défaut de ChromaDB qui tourne sur
ONNX (bien plus léger que PyTorch) pour éviter les crash OOM sur Render.
"""
from functools import lru_cache
from typing import List

@lru_cache(maxsize=1)
def _get_model():
    from chromadb.utils import embedding_functions
    # DefaultEmbeddingFunction utilise all-MiniLM-L6-v2 via onnxruntime
    return embedding_functions.DefaultEmbeddingFunction()


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Encode une liste de textes en vecteurs."""
    model = _get_model()
    # Le modèle Chroma attend une liste et renvoie une liste de listes
    return model(texts)


def embed_query(text: str) -> List[float]:
    """Encode une seule requête."""
    return embed_texts([text])[0]

"""Génération d'embeddings via sentence-transformers (all-MiniLM-L6-v2).

Le modèle est chargé une seule fois (singleton) car son chargement est coûteux.
"""
from functools import lru_cache
from typing import List

MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Encode une liste de textes en vecteurs."""
    model = _get_model()
    vectors = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return vectors.tolist()


def embed_query(text: str) -> List[float]:
    """Encode une seule requête."""
    return embed_texts([text])[0]

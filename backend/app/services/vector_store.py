"""Wrapper autour de ChromaDB (PersistentClient)."""
from functools import lru_cache
from typing import Dict, List

from app.config import settings


@lru_cache(maxsize=1)
def _get_collection():
    import chromadb

    client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    # On fournit nous-mêmes les embeddings -> pas de fonction d'embedding interne.
    return client.get_or_create_collection(
        name=settings.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _clean_metadata(chunk: Dict) -> Dict:
    """Prépare des métadonnées compatibles Chroma (pas de None)."""
    return {
        "source": chunk.get("source") or "",
        "symbol": chunk.get("symbol") or "",
        "line": int(chunk.get("line") or 0),
        "kind": chunk.get("kind") or "doc",
        "node_type": chunk.get("node_type") or "",
    }


def reset() -> None:
    """Vide la collection (l'outil gère un seul dépôt à la fois)."""
    import chromadb

    client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    try:
        client.delete_collection(settings.COLLECTION_NAME)
    except Exception:
        pass  # la collection peut ne pas exister encore
    # Invalide le cache pour recréer une collection vide au prochain accès
    _get_collection.cache_clear()


def add_chunks(chunks: List[Dict], embeddings: List[List[float]]) -> None:
    """Ajoute des chunks + embeddings à la collection."""
    if not chunks:
        return

    collection = _get_collection()
    base = collection.count()
    ids = [f"chunk-{base + i}" for i in range(len(chunks))]
    documents = [c["text"] for c in chunks]
    metadatas = [_clean_metadata(c) for c in chunks]

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def query(embedding: List[float], top_k: int) -> List[Dict]:
    """Recherche les top_k chunks les plus proches. Retourne texte + métadonnées."""
    collection = _get_collection()
    if collection.count() == 0:
        return []

    result = collection.query(
        query_embeddings=[embedding],
        n_results=min(top_k, collection.count()),
    )

    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]

    out: List[Dict] = []
    for doc, meta in zip(documents, metadatas):
        out.append({"text": doc, "metadata": meta})
    return out


def count() -> int:
    """Nombre de chunks indexés."""
    return _get_collection().count()

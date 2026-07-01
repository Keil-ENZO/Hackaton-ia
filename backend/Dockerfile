FROM python:3.11

# git : requis par git_service.py pour cloner les repos à indexer
# libgomp1 : requis par PyTorch (sentence-transformers) pour OpenMP
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Mise à jour de pip (évite les erreurs de wheel legacy)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Dépendances Python (cache Docker si requirements.txt n'a pas changé)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pré-télécharge le modèle d'embeddings pour éviter la latence au 1er appel
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

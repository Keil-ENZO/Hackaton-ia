# DevOnboard Copilot

Un copilote IA pour l'onboarding développeur. Colle l'URL d'un dépôt **GitHub public** :
l'app le clone, indexe le code (extraction AST) et la doc, puis répond à tes questions dans
un chat en **citant précisément ses sources** (fichier, symbole, numéro de ligne).

> Projet hackathon étudiant (7h). Pas de base relationnelle, pas d'auth, pas d'historique persistant.

---

## Stack

| Couche          | Techno                                                          |
| --------------- | -------------------------------------------------------------- |
| Backend         | FastAPI (Python 3.11+)                                          |
| Frontend        | Next.js 14 (App Router) + TypeScript + Tailwind CSS            |
| LLM             | Groq API — `llama-3.3-70b-versatile` (SDK `groq`)             |
| Base vectorielle| ChromaDB (`PersistentClient`, local)                           |
| Embeddings      | `sentence-transformers` · `all-MiniLM-L6-v2` (local, gratuit) |
| Parsing code    | `tree-sitter-language-pack` (AST multi-langage)               |

### Endpoints

| Méthode | Route     | Rôle                                                        |
| ------- | --------- | ----------------------------------------------------------- |
| `POST`  | `/ingest` | Clone → parse → embed → indexe un repo (synchrone)          |
| `POST`  | `/chat`   | Recherche top-5 + génération Groq + sources citées          |
| `GET`   | `/health` | Statut + nombre de chunks indexés (réveil du service)       |

---

## Arborescence

```
Hackaton-ia/
├── backend/          # FastAPI
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── models.py
│       ├── routes/   # ingest, chat, health
│       └── services/ # git, file_walker, chunkers, embeddings, vector_store, llm
├── frontend/         # Next.js 14
│   ├── app/          # layout, page, globals.css
│   ├── components/   # IngestPanel, ChatPanel, ChatMessage, SourceChip
│   └── lib/          # api.ts, types.ts
├── docker-compose.yml (optionnel)
└── README.md
```

---

## Lancement en local

### Prérequis
- Python 3.11+
- Node.js 20+
- `git` installé et disponible dans le `PATH`
- Une clé API Groq : https://console.groq.com/keys

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # puis édite GROQ_API_KEY
uvicorn app.main:app --reload --port 8000
```

Le backend écoute sur `http://localhost:8000` (docs interactives : `/docs`).

> ⚠️ Au premier `/ingest` ou `/chat`, le modèle `all-MiniLM-L6-v2` (~90 Mo) est
> téléchargé une seule fois. Prévois quelques secondes.

Variables `backend/.env` :

| Variable            | Défaut                      | Description                          |
| ------------------- | --------------------------- | ------------------------------------ |
| `GROQ_API_KEY`      | —                           | **Obligatoire**                      |
| `GROQ_MODEL`        | `llama-3.3-70b-versatile`   | Modèle Groq                          |
| `CHROMA_PERSIST_DIR`| `./chroma_store`            | Dossier de persistance ChromaDB      |

### 2. Frontend

```bash
cd frontend
npm install

cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Ouvre `http://localhost:3000`.

### 3. Utilisation
1. Colle une URL GitHub publique (ex. `https://github.com/tiangolo/fastapi`) → **Indexer**.
2. Une fois l'indexation terminée, pose tes questions dans le chat.
3. Chaque réponse affiche ses sources sous forme d'étiquettes `fichier::symbole (ligne X)`.

### Docker (le plus simple)

Une seule commande, pas besoin d'installer Python ni Node localement :

```bash
cp .env.example .env        # puis édite GROQ_API_KEY à la racine
docker compose up --build
```

- Frontend : http://localhost:3000
- Backend  : http://localhost:8000/docs

Le modèle d'embeddings est pré-téléchargé dans l'image backend (1er build un peu long,
puis démarrage rapide). L'index ChromaDB est conservé dans le volume `chroma_data` entre
les redémarrages. Pour tout réinitialiser : `docker compose down -v`.

---

## Déploiement

### Backend → Render

1. Crée un **Web Service** sur [Render](https://render.com) pointant sur ce repo, racine `backend/`.
2. **Build command** :
   ```bash
   pip install -r requirements.txt
   ```
3. **Start command** :
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. **Environment** : Python 3.11. Ajoute `git` si besoin (image Render standard l'inclut).
5. **Variables d'environnement** : `GROQ_API_KEY`, `GROQ_MODEL`, `CHROMA_PERSIST_DIR=/var/data/chroma`.
6. (Recommandé) Ajoute un **disque persistant** monté sur `/var/data` pour conserver l'index
   entre les redéploiements.

> 💤 Le plan gratuit Render met le service en veille après 15 min d'inactivité. Avant une démo,
> réveille-le en appelant `GET /health` (le frontend le fait automatiquement au chargement).

### Frontend → Vercel

1. Importe le repo sur [Vercel](https://vercel.com), **Root Directory** = `frontend/`.
2. Framework détecté automatiquement : **Next.js**.
3. Variable d'environnement :
   ```
   NEXT_PUBLIC_API_URL = https://<ton-service>.onrender.com
   ```
4. Déploie. Le CORS backend est ouvert (`*`) — pense à le restreindre à ton domaine Vercel en prod.

---

## Détails d'implémentation

### Pipeline d'ingestion (`POST /ingest`, synchrone)
1. Validation : le domaine doit être `github.com`.
2. Clone shallow (`git clone --depth 1`) dans un dossier temporaire.
3. Parcours de l'arbo en excluant `.git`, `node_modules`, `venv`, `dist`, `build`,
   `__pycache__` et tout fichier > 500 Ko.
4. Chunking selon l'extension :
   - **Code** (`.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.java`) → extraction AST via
     tree-sitter (fonctions, classes, méthodes). Config par extension **facilement extensible**
     dans `services/chunker_code.py`. Fallback texte si langage inconnu ou parsing en échec.
   - **Doc / autres** (`.md`, `.txt`, `.rst`, …) → chunking par paragraphe (~800 c, chevauchement ~150 c).
5. Embeddings via sentence-transformers.
6. Stockage dans ChromaDB avec métadonnées (`source`, `symbol`, `line`, `kind`, `node_type`).
7. Suppression du clone temporaire.
8. Retour d'un résumé (fichiers, chunks, langages).

### Chat (`POST /chat`)
- Embed de la question → recherche des 5 chunks les plus proches (cosine).
- Prompt système strict : interdiction d'inventer hors du contexte fourni.
- Réponse Groq + liste de sources dédupliquées au format `fichier::symbole (ligne X)` (code)
  ou `fichier` (doc).

### Étendre le support d'un langage
Ajoute une entrée dans `LANGUAGE_CONFIG` (`backend/app/services/chunker_code.py`) :
```python
".go": {"lang": "go", "nodes": ["function_declaration", "method_declaration", "type_declaration"]},
```
et l'extension dans `CODE_EXTENSIONS` (déjà dérivée automatiquement de `LANGUAGE_CONFIG`).
```

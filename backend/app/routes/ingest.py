"""POST /ingest — clone, parse, embed et indexe un repo GitHub public (synchrone)."""
import os

from fastapi import APIRouter, HTTPException

from app.models import IngestRequest, IngestResponse
from app.services import embeddings, git_service, vector_store
from app.services.chunker_code import LANGUAGE_CONFIG, chunk_code
from app.services.chunker_config import chunk_config
from app.services.chunker_markdown import chunk_markdown
from app.services.chunker_text import chunk_text
from app.services.file_walker import walk_repo

router = APIRouter()

CODE_EXTENSIONS = set(LANGUAGE_CONFIG.keys())

# Fichiers de documentation structurée (Markdown, reStructuredText)
MARKDOWN_EXTENSIONS = {".md", ".mdx", ".rst"}

# Fichiers de configuration / infrastructure
CONFIG_EXTENSIONS = {
    ".yml", ".yaml",           # Docker Compose, GitHub Actions, Ansible…
    ".json",                   # package.json, tsconfig, manifest…
    ".toml",                   # pyproject.toml, Cargo.toml…
    ".ini", ".cfg", ".conf",   # configs applicatives
    ".sh", ".bash", ".zsh",   # scripts shell
    ".env",                    # variables d’environnement
    ".properties",             # Java / Spring
    ".xml",                    # Maven pom.xml, Android…
    ".tf",                     # Terraform
    ".hcl",                    # HCL (Terraform/Vault)
}

# Noms de fichiers spéciaux à traiter comme config quel que soit leur suffixe
CONFIG_NAMES = {
    "dockerfile", "makefile", "procfile", "jenkinsfile",
    "vagrantfile", "rakefile", ".env.example", ".env.sample",
    ".env.local.example", ".env.local", ".editorconfig", ".gitignore",
    ".dockerignore",
}


# Mots-clés sémantiques ajoutés au header des chunks config
# pour améliorer la similarité cosine face aux questions opérationnelles
_CONFIG_HINTS: dict[str, str] = {
    "docker-compose": "démarrer lancer stack services ports volumes environnement",
    "dockerfile":     "build image docker déploiement conteneur",
    "makefile":       "commandes targets build démarrer lancer scripts",
    ".github/workflows": "CI CD pipeline workflow GitHub Actions tests déploiement automatique build deploy",
    "workflows":      "CI CD pipeline workflow GitHub Actions tests déploiement automatique",
    "requirements":   "dépendances packages python installer pip",
    "package.json":   "dépendances npm scripts node lancer démarrer",
    "pyproject":      "dépendances configuration python build",
    ".env":           "variables environnement configuration clés secrets",
    "readme":         "documentation installation lancement utilisation guide",
    "nginx":          "serveur proxy configuration reverse-proxy",
    "ansible":        "déploiement provisioning infrastructure",
}


def _get_config_hint(source: str) -> str:
    """Retourne des mots-clés sémantiques pour un fichier config selon son chemin."""
    src_lower = source.lower()
    for key, hint in _CONFIG_HINTS.items():
        if key in src_lower:
            return hint
    return ""


def _embed_input(chunk: dict) -> str:
    """Construit le texte réellement vectorisé : chemin (+ symbole) puis contenu.

    - Pour les chunks code : chemin :: symbole + texte
    - Pour les chunks config : chemin + mots-clés sémantiques + texte
      (crucial pour que « comment démarrer » matche docker-compose.yml)
    - Pour la doc Markdown : chemin :: titre_section + texte
    """
    source = chunk.get("source") or ""
    symbol = chunk.get("symbol")
    kind = chunk.get("kind", "doc")

    if kind == "config":
        hint = _get_config_hint(source)
        header = f"[CONFIG] {source}"
        if hint:
            header += f" | {hint}"
    elif symbol:
        header = f"{source} :: {symbol}"
    else:
        header = source

    return f"{header}\n{chunk['text']}"


def _read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


@router.post("/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest) -> IngestResponse:
    # 1. Validation de l'URL
    try:
        repo_url = git_service.validate_github_url(payload.repo_url)
    except git_service.GitError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # URL web (sans .git) + nom owner/repo, pour les liens cliquables côté front
    repo_web_url = repo_url[:-4] if repo_url.endswith(".git") else repo_url
    repo_name = "/".join(repo_web_url.rstrip("/").split("/")[-2:])

    # 2. Clone shallow
    try:
        repo_path = git_service.clone_shallow(repo_url)
    except git_service.GitError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    files_indexed = 0
    all_chunks = []
    languages = set()

    try:
        # 3-4. Parcours + chunking
        for abs_path, rel_path in walk_repo(repo_path):
            ext = os.path.splitext(rel_path)[1].lower()
            filename_lower = os.path.basename(rel_path).lower()
            content = _read_file(abs_path)
            if not content.strip():
                continue

            # Fichiers de code : AST tree-sitter
            if ext in CODE_EXTENSIONS:
                chunks = chunk_code(content, rel_path, ext)
                languages.add(LANGUAGE_CONFIG[ext]["lang"])

            # Markdown / RST : chunker par sections (garde titre + contenu ensemble)
            elif ext in MARKDOWN_EXTENSIONS:
                chunks = chunk_markdown(content, rel_path)

            # Config / infra : YAML, JSON, Dockerfile, Makefile, .env…
            elif ext in CONFIG_EXTENSIONS or filename_lower in CONFIG_NAMES:
                chunks = chunk_config(content, rel_path, ext)

            # Texte brut (.txt, autres)
            else:
                chunks = chunk_text(content, rel_path)

            if chunks:
                all_chunks.extend(chunks)
                files_indexed += 1

        if not all_chunks:
            raise HTTPException(
                status_code=422,
                detail="Aucun contenu indexable trouvé dans ce dépôt.",
            )

        # 5. Embeddings — on vectorise une version ENRICHIE (chemin + symbole en
        #    tête) pour que les questions en langage naturel matchent le code et
        #    les fichiers de config, pas seulement la doc. Le document stocké et
        #    envoyé au LLM reste le texte brut d'origine.
        texts = [_embed_input(c) for c in all_chunks]
        vectors = embeddings.embed_texts(texts)

        # 6. Stockage ChromaDB — on remplace l'index précédent (un dépôt à la fois)
        vector_store.reset()
        vector_store.add_chunks(all_chunks, vectors)

    finally:
        # 7. Nettoyage du clone temporaire
        git_service.cleanup(repo_path)

    return IngestResponse(
        files_indexed=files_indexed,
        chunks_created=len(all_chunks),
        languages=sorted(languages),
        message=(
            f"Dépôt indexé : {files_indexed} fichiers, "
            f"{len(all_chunks)} chunks."
        ),
        repo_url=repo_web_url,
        repo_name=repo_name,
    )

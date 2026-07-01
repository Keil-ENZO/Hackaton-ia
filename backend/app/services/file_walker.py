"""Parcours de l'arborescence d'un repo cloné avec exclusions et limite de taille."""
import os
from typing import Iterator, Tuple

from app.config import settings

EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "dist",
    "build",
    "__pycache__",
    ".next",
    ".cache",
    "coverage",
}

# Extensions binaires courantes à ignorer d'office
# NB : .lock RETIRÉ — certains Pipfile.lock / poetry.lock sont utiles
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
    ".pdf", ".zip", ".gz", ".tar", ".mp4", ".mp3", ".woff",
    ".woff2", ".ttf", ".eot", ".bin", ".so", ".dll", ".pyc",
    ".class", ".map",
}

# Fichiers config/infra sans extension ou avec nom particulier — toujours indexés
CONFIG_FILENAMES = {
    "dockerfile", "makefile", "procfile", "jenkinsfile",
    ".env.example", ".env.sample", ".env.local.example",
    "docker-compose.yml", "docker-compose.yaml",
    "docker-compose.override.yml",
}


def walk_repo(root: str) -> Iterator[Tuple[str, str]]:
    """Génère (chemin_absolu, chemin_relatif) pour chaque fichier retenu.

    Exclut les dossiers listés, les fichiers binaires et ceux > MAX_FILE_SIZE.
    Inclut explicitement tous les fichiers config/infra (YAML, JSON, TOML,
    Dockerfile, Makefile, .env.example…).
    """
    for dirpath, dirnames, filenames in os.walk(root):
        # Élague les dossiers exclus (modification in-place de dirnames)
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]

        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            name_lower = filename.lower()

            # Toujours exclure les binaires
            if ext in BINARY_EXTENSIONS:
                continue

            # Exclure les .lock sauf s'ils sont < 50 Ko (Pipfile.lock utile)
            if ext == ".lock":
                abs_path = os.path.join(dirpath, filename)
                try:
                    if os.path.getsize(abs_path) > 50 * 1024:
                        continue
                except OSError:
                    continue

            abs_path = os.path.join(dirpath, filename)
            try:
                if os.path.getsize(abs_path) > settings.MAX_FILE_SIZE:
                    continue
            except OSError:
                continue

            rel_path = os.path.relpath(abs_path, root)
            yield abs_path, rel_path

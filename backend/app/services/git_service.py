"""Validation et clonage shallow d'un repo GitHub public."""
import shutil
import subprocess
import tempfile
from urllib.parse import urlparse


class GitError(Exception):
    """Erreur de validation ou de clonage."""


def validate_github_url(repo_url: str) -> str:
    """Valide que l'URL pointe vers github.com. Retourne l'URL nettoyée."""
    url = repo_url.strip()
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise GitError("L'URL doit commencer par http(s)://")

    host = (parsed.netloc or "").lower()
    if host not in ("github.com", "www.github.com"):
        raise GitError("Seuls les dépôts github.com sont autorisés.")

    # Extrait owner/repo, en ignorant tout suffixe de navigation
    # (/tree/<branch>, /blob/<...>, /pull/..., slash final, .git)
    segments = [s for s in parsed.path.split("/") if s]
    if len(segments) < 2:
        raise GitError("URL de dépôt GitHub invalide (owner/repo manquant).")

    owner, repo = segments[0], segments[1]
    repo = repo[:-4] if repo.endswith(".git") else repo

    # Reconstruit une URL de clone canonique
    return f"https://github.com/{owner}/{repo}.git"


def clone_shallow(repo_url: str) -> str:
    """Clone le repo en shallow dans un dossier temporaire. Retourne le chemin."""
    tmp_dir = tempfile.mkdtemp(prefix="devonboard_")
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, tmp_dir],
            check=True,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except subprocess.CalledProcessError as exc:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise GitError(f"Échec du clonage : {exc.stderr.strip() or exc}") from exc
    except subprocess.TimeoutExpired as exc:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise GitError("Le clonage a dépassé le délai imparti.") from exc

    return tmp_dir


def cleanup(path: str) -> None:
    """Supprime le dossier temporaire du clone."""
    shutil.rmtree(path, ignore_errors=True)

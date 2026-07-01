import re
from typing import Dict, List, Optional

try:
    import yaml as _yaml  # PyYAML — présent dans requirements.txt
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

MAX_CONFIG_CHUNK = 1500  # Taille max d'un bloc config (augmentée pour les workflows)

# Taille au-delà de laquelle on ne garde PAS le fichier entier
MAX_WHOLE_FILE = 3000


def _extract_yaml_symbol(content: str) -> Optional[str]:
    """Extrait le nom + déclencheurs d'un fichier YAML GitHub Actions.

    Ex : 'CI · déclenché par push pull_request' — utilisé comme symbol
    pour enrichir l'embedding avec un signal sémantique fort.
    """
    if _YAML_AVAILABLE:
        try:
            data = _yaml.safe_load(content)
            if not isinstance(data, dict):
                raise ValueError("not a dict")
            parts = []
            name = data.get("name")
            if name:
                parts.append(str(name))
            on_val = data.get("on") or data.get(True)  # YAML parse 'on' comme True
            if on_val:
                if isinstance(on_val, dict):
                    parts.append("déclenché par " + " ".join(on_val.keys()))
                elif isinstance(on_val, list):
                    parts.append("déclenché par " + " ".join(on_val))
                elif isinstance(on_val, str):
                    parts.append("déclenché par " + on_val)
            jobs = data.get("jobs", {})
            if isinstance(jobs, dict) and jobs:
                parts.append("jobs: " + ", ".join(list(jobs.keys())[:5]))
            return " · ".join(parts) if parts else None
        except Exception:
            pass  # Fallback regex ci-dessous

    # Fallback regex (sans PyYAML ou si parsing échoue)
    name_m = re.search(r"^name:\s*(.+)$", content, re.MULTILINE)
    jobs_m = re.findall(r"^  ([a-zA-Z_][a-zA-Z0-9_-]*):\s*$", content, re.MULTILINE)
    triggers_m = re.findall(r"^\s{2,4}([a-z_]+):\s*$", content, re.MULTILINE)
    symbol_parts = []
    if name_m:
        symbol_parts.append(name_m.group(1).strip())
    if triggers_m:
        symbol_parts.append("déclenché par " + " ".join(triggers_m[:4]))
    if jobs_m:
        symbol_parts.append("jobs: " + ", ".join(jobs_m[:5]))
    return " · ".join(symbol_parts) if symbol_parts else None



def _is_github_actions(content: str, rel_path: str) -> bool:
    """Détecte si un fichier YAML est un workflow GitHub Actions."""
    path_lower = rel_path.lower()
    if ".github/workflows" in path_lower or ".github\\workflows" in path_lower:
        return True
    # Détection par contenu (clé 'on' + 'jobs' = GitHub Actions)
    has_on = bool(re.search(r"^on:\s*$|^on:\s+", content, re.MULTILINE))
    has_jobs = bool(re.search(r"^jobs:\s*$", content, re.MULTILINE))
    return has_on and has_jobs


def _split_yaml_blocks(content: str) -> List[str]:
    """Sépare un fichier YAML générique sur les séparateurs `---`.

    NE PAS utiliser pour les GitHub Actions (coupebraient trop fin).
    """
    # Séparateurs YAML explicites
    blocks = re.split(r"^---\s*$", content, flags=re.MULTILINE)
    result = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if len(block) <= MAX_CONFIG_CHUNK:
            result.append(block)
        else:
            # Découpe sur les clés de premier niveau (ex: `services:`, `volumes:`)
            parts = re.split(r"\n(?=[a-zA-Z_][a-zA-Z0-9_-]*:)", block)
            result.extend(p.strip() for p in parts if p.strip())
    return result


def chunk_config(content: str, rel_path: str, ext: str = "") -> List[Dict]:
    """Indexe un fichier config/infra avec kind='config'.

    Stratégie par type :
    - GitHub Actions YAML : fichier entier + symbole riche (name + triggers + jobs)
    - docker-compose / YAML générique : split sur `---` ou clés 1er niveau
    - Dockerfile : split sur les stages FROM
    - Makefile : split sur les targets
    - JSON/TOML/autres : entier si < MAX_WHOLE_FILE
    """
    filename = rel_path.split("/")[-1].lower()

    # --- GitHub Actions YAML : JAMAIS fragmenter, garder tout le workflow ---
    if ext in (".yml", ".yaml") and _is_github_actions(content, rel_path):
        symbol = _extract_yaml_symbol(content)
        # Si le fichier est trop grand (rare), on le tronque proprement
        text = content.strip() if len(content) <= MAX_WHOLE_FILE else content[:MAX_WHOLE_FILE].strip()
        return [
            {
                "text": text,
                "source": rel_path,
                "symbol": symbol,
                "line": 1,
                "kind": "config",
                "node_type": "github_actions_workflow",
            }
        ]

    # --- YAML générique (docker-compose, ansible, helm…) ---
    if ext in (".yml", ".yaml"):
        # Si le fichier est court, garder entier
        if len(content.strip()) <= MAX_WHOLE_FILE:
            return [
                {
                    "text": content.strip(),
                    "source": rel_path,
                    "symbol": None,
                    "line": 1,
                    "kind": "config",
                    "node_type": "yaml_file",
                }
            ]
        blocks = _split_yaml_blocks(content)
        if not blocks:
            blocks = [content.strip()]
        return [
            {
                "text": block,
                "source": rel_path,
                "symbol": None,
                "line": 1,
                "kind": "config",
                "node_type": "yaml_block",
            }
            for block in blocks
            if block
        ]

    # --- Dockerfile ---
    if "dockerfile" in filename:
        # Sépare sur les instructions FROM / RUN / COPY / CMD (stages)
        stages = re.split(r"(?m)^(?=FROM\s)", content)
        blocks = []
        for stage in stages:
            stage = stage.strip()
            if not stage:
                continue
            if len(stage) <= MAX_CONFIG_CHUNK:
                blocks.append(stage)
            else:
                # Coupe sur chaque instruction
                instructions = re.split(r"(?m)^(?=RUN |COPY |ADD |ENV |EXPOSE )", stage)
                blocks.extend(i.strip() for i in instructions if i.strip())
        return [
            {
                "text": b,
                "source": rel_path,
                "symbol": None,
                "line": 1,
                "kind": "config",
                "node_type": "dockerfile_stage",
            }
            for b in blocks
            if b
        ] or [{"text": content.strip(), "source": rel_path, "symbol": None, "line": 1, "kind": "config", "node_type": "dockerfile_stage"}]

    # --- Makefile ---
    if "makefile" in filename:
        # Sépare sur les targets (`target:`)
        targets = re.split(r"(?m)^(?=[a-zA-Z_][a-zA-Z0-9_-]*:)", content)
        return [
            {
                "text": t.strip(),
                "source": rel_path,
                "symbol": re.match(r"^([a-zA-Z_][a-zA-Z0-9_-]*)", t.strip()).group(1) if re.match(r"^([a-zA-Z_][a-zA-Z0-9_-]*)", t.strip()) else None,
                "line": 1,
                "kind": "config",
                "node_type": "makefile_target",
            }
            for t in targets
            if t.strip()
        ]

    # --- JSON / TOML / .env* / autres ---
    if len(content) <= MAX_CONFIG_CHUNK:
        return [
            {
                "text": content.strip(),
                "source": rel_path,
                "symbol": None,
                "line": 1,
                "kind": "config",
                "node_type": "config_file",
            }
        ]

    # Fichier trop long : split par paragraphe
    from app.services.chunker_text import chunk_text
    chunks = chunk_text(content, rel_path)
    for c in chunks:
        c["kind"] = "config"
    return chunks

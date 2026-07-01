"""Chunking de code via l'AST (tree-sitter-language-pack) avec fallback texte."""
from typing import Dict, List, Optional

from app.services.chunker_text import chunk_text

# Config modulaire par extension — facilement extensible.
LANGUAGE_CONFIG: Dict[str, Dict] = {
    ".py": {
        "lang": "python",
        "nodes": ["function_definition", "class_definition"],
    },
    ".js": {
        "lang": "javascript",
        "nodes": ["function_declaration", "method_definition", "class_declaration"],
    },
    ".jsx": {
        "lang": "javascript",
        "nodes": ["function_declaration", "method_definition", "class_declaration"],
    },
    ".ts": {
        "lang": "typescript",
        "nodes": ["function_declaration", "method_definition", "class_declaration"],
    },
    ".tsx": {
        "lang": "tsx",
        "nodes": ["function_declaration", "method_definition", "class_declaration"],
    },
    ".java": {
        "lang": "java",
        "nodes": ["method_declaration", "class_declaration", "interface_declaration"],
    },
}


def _extract_symbol_name(node) -> Optional[str]:
    """Récupère le nom (identifier) d'un nœud fonction/classe si présent."""
    name_node = node.child_by_field_name("name")
    if name_node is not None:
        return name_node.text.decode("utf-8", errors="ignore")
    # Fallback : premier enfant de type identifier
    for child in node.children:
        if "identifier" in child.type:
            return child.text.decode("utf-8", errors="ignore")
    return None


def chunk_code(content: str, rel_path: str, ext: str) -> List[Dict]:
    """Extrait les nœuds AST pertinents comme chunks.

    Fallback vers chunk_text si le langage n'est pas configuré ou si le
    parsing échoue.
    """
    config = LANGUAGE_CONFIG.get(ext)
    if config is None:
        return chunk_text(content, rel_path)

    try:
        from tree_sitter_language_pack import get_parser

        parser = get_parser(config["lang"])
        source_bytes = content.encode("utf-8")
        tree = parser.parse(source_bytes)
    except Exception:
        return chunk_text(content, rel_path)

    target_nodes = set(config["nodes"])
    chunks: List[Dict] = []

    # Parcours en profondeur de l'arbre
    def visit(node) -> None:
        if node.type in target_nodes:
            text = node.text.decode("utf-8", errors="ignore")
            if text.strip():
                chunks.append(
                    {
                        "text": text,
                        "source": rel_path,
                        "symbol": _extract_symbol_name(node),
                        "line": node.start_point[0] + 1,  # 0-indexé -> 1-indexé
                        "kind": "code",
                        "node_type": node.type,
                    }
                )
            # On ne descend pas dans les méthodes d'une classe déjà capturée
            # sauf si elles ne sont pas déjà des chunks — ici on descend
            # quand même pour capturer méthodes imbriquées.
        for child in node.children:
            visit(child)

    visit(tree.root_node)

    # Si aucun nœud pertinent trouvé, fallback texte pour ne pas perdre le fichier
    if not chunks:
        return chunk_text(content, rel_path)

    return chunks

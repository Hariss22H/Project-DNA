import ast
from pathlib import Path
from typing import Dict, List, Any
from app.services.local_repository_service import REPO_ROOT, repository_service


class GraphService:
    def generate(self) -> Dict[str, Any]:
        """Generate structured JSON representing a Knowledge Graph of the project."""
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        seen_ids: set = set()

        def add_node(node_id: str, label: str, node_type: str) -> None:
            if node_id not in seen_ids:
                seen_ids.add(node_id)
                nodes.append({"id": node_id, "label": label, "type": node_type})

        def add_edge(source: str, target: str, relation: str) -> None:
            edges.append({"source": source, "target": target, "relation": relation})

        # Root Node
        add_node("repo_root", REPO_ROOT.name, "Repository")

        folders = repository_service.get_folders()
        files = repository_service.get_files()

        for folder in folders:
            folder_id = folder["path"]
            add_node(folder_id, folder["name"], "Folder")

            parent = str(Path(folder_id).parent.as_posix())
            if parent == ".":
                add_edge("repo_root", folder_id, "Contains")
            else:
                add_edge(parent, folder_id, "Contains")

        for file in files:
            file_id = file["path"]
            add_node(file_id, file["name"], "File")

            parent = str(Path(file_id).parent.as_posix())
            if parent == ".":
                add_edge("repo_root", file_id, "Contains")
            else:
                add_edge(parent, file_id, "Contains")

            # AST extraction for Python files — classes and top-level functions only
            if file["extension"] == ".py":
                try:
                    full_path = REPO_ROOT / file_id
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        source = f.read()

                    tree = ast.parse(source)
                    # Only walk top-level body to avoid duplicate nested entries
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            class_id = f"{file_id}::{node.name}"
                            add_node(class_id, node.name, "Class")
                            add_edge(file_id, class_id, "Contains")
                        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            func_id = f"{file_id}::{node.name}"
                            add_node(func_id, node.name, "Function")
                            add_edge(file_id, func_id, "Contains")
                except Exception:
                    pass  # Ignore unparseable Python files

        return {
            "nodes": nodes,
            "edges": edges,
        }


graph_service = GraphService()

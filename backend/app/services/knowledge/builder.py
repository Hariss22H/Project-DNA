"""Semantic knowledge graph builder with meaningful relationships."""

from __future__ import annotations

from app.services.knowledge.base import (
    GraphEdge,
    GraphNode,
    KnowledgeGraphBuilder,
    KnowledgeGraphData,
    ProjectEntity,
)
from app.services.knowledge.semantics import RELATION_TEMPLATES

ALLOWED_TYPES = {
    "file",
    "module",
    "technology",
    "api",
    "document",
    "feature",
    "repository",
    "other",
}


class DefaultKnowledgeGraphBuilder(KnowledgeGraphBuilder):
    async def build_graph(
        self,
        *,
        project_id: str,
        entities: list[ProjectEntity],
    ) -> KnowledgeGraphData:
        root_id = f"project:{project_id}"
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        node_ids: set[str] = set()
        by_name: dict[str, ProjectEntity] = {}

        def add_node(entity: ProjectEntity) -> None:
            if entity.id in node_ids:
                return
            node_type = entity.entity_type if entity.entity_type in ALLOWED_TYPES else "other"
            nodes.append(
                GraphNode(
                    id=entity.id,
                    label=entity.name,
                    type=node_type,  # type: ignore[arg-type]
                    data={
                        **entity.metadata,
                        "entity_type": entity.entity_type,
                        "summary": _node_summary(entity),
                    },
                )
            )
            node_ids.add(entity.id)
            by_name[entity.name.lower()] = entity

        def add_edge(
            source: str,
            target: str,
            *,
            relation: str,
            label: str | None = None,
            explanation: str | None = None,
        ) -> None:
            if source not in node_ids or target not in node_ids or source == target:
                return
            edge_id = f"{source}:{relation}:{target}"
            if any(edge.id == edge_id for edge in edges):
                return
            edges.append(
                GraphEdge(
                    id=edge_id,
                    source=source,
                    target=target,
                    label=label or relation.replace("_", " "),
                    relation=relation,
                    data={
                        "explanation": explanation
                        or f"{_label(source, nodes)} {label or relation.replace('_', ' ')} {_label(target, nodes)}",
                    },
                )
            )

        if not any(entity.id == root_id for entity in entities):
            add_node(
                ProjectEntity(
                    id=root_id,
                    name="Project",
                    entity_type="repository",
                    metadata={"project_id": project_id},
                )
            )

        for entity in entities:
            add_node(entity)

        repo_nodes = [e for e in entities if e.entity_type == "repository" and e.id != root_id]
        modules = [e for e in entities if e.entity_type == "module"]
        techs = [e for e in entities if e.entity_type == "technology"]
        apis = [e for e in entities if e.entity_type == "api"]
        docs = [e for e in entities if e.entity_type == "document"]
        features = [e for e in entities if e.entity_type == "feature"]

        for repo in repo_nodes:
            add_edge(
                root_id,
                repo.id,
                relation="has_repository",
                label="has repo",
                explanation=f"Project is linked to repository {repo.name}.",
            )

        for module in modules:
            add_edge(
                root_id,
                module.id,
                relation="includes_module",
                label="includes",
                explanation=f"Project includes the {module.name} module.",
            )

        for tech in techs:
            # Prefer attaching tech to a related module when possible.
            owner = _preferred_owner(tech.name, by_name) or root_id
            add_edge(
                owner if owner in node_ids else root_id,
                tech.id,
                relation="uses",
                label="uses",
                explanation=f"{_name_from_id(owner, by_name, fallback='Project')} uses {tech.name}.",
            )

        for feature in features:
            add_edge(
                root_id,
                feature.id,
                relation="includes_feature",
                label="includes",
                explanation=f"Project includes feature {feature.name}.",
            )

        for api in apis:
            backend = by_name.get("backend")
            source = backend.id if backend else root_id
            add_edge(
                source,
                api.id,
                relation="exposes",
                label="exposes",
                explanation=f"{backend.name if backend else 'Project'} exposes {api.name}.",
            )

        for doc in docs:
            add_edge(
                root_id,
                doc.id,
                relation="documented_by",
                label="documented by",
                explanation=f"Project knowledge includes document {doc.name}.",
            )
            # Documents describe nearby modules/features when names overlap.
            for module in modules:
                if module.name.lower() in doc.name.lower() or module.name.lower() in str(doc.metadata):
                    add_edge(
                        doc.id,
                        module.id,
                        relation="documents",
                        label="documents",
                        explanation=f"{doc.name} documents {module.name}.",
                    )
            if "readme" in doc.name.lower():
                for target_name in ("Authentication", "Backend", "Frontend", "Deployment", "REST API"):
                    target = by_name.get(target_name.lower())
                    if target:
                        add_edge(
                            doc.id,
                            target.id,
                            relation="documents",
                            label="documents",
                            explanation=f"README documents {target.name}.",
                        )

        # Apply curated semantic relationships when both ends exist.
        for left, right, relation, label in RELATION_TEMPLATES:
            left_entity = by_name.get(left.lower())
            right_entity = by_name.get(right.lower())
            if not left_entity or not right_entity:
                continue
            add_edge(
                left_entity.id,
                right_entity.id,
                relation=relation,
                label=label,
                explanation=f"{left} {label} {right}.",
            )

        return KnowledgeGraphData(nodes=nodes, edges=edges)


def _preferred_owner(tech_name: str, by_name: dict[str, ProjectEntity]) -> str | None:
    mapping = {
        "fastapi": "backend",
        "flask": "backend",
        "django": "backend",
        "mongodb": "backend",
        "postgresql": "backend",
        "qdrant": "knowledge twin",
        "openai": "knowledge twin",
        "gemini": "knowledge twin",
        "react": "frontend",
        "vite": "frontend",
        "next.js": "frontend",
        "jwt": "authentication",
        "oauth": "authentication",
        "docker": "deployment",
        "kubernetes": "deployment",
        "pytest": "testing",
    }
    owner_name = mapping.get(tech_name.lower())
    if not owner_name:
        return None
    owner = by_name.get(owner_name)
    return owner.id if owner else None


def _name_from_id(node_id: str, by_name: dict[str, ProjectEntity], *, fallback: str) -> str:
    for entity in by_name.values():
        if entity.id == node_id:
            return entity.name
    return fallback


def _label(node_id: str, nodes: list[GraphNode]) -> str:
    for node in nodes:
        if node.id == node_id:
            return node.label
    return node_id


def _node_summary(entity: ProjectEntity) -> str:
    kind = entity.entity_type.replace("_", " ")
    source = entity.metadata.get("source") or "project knowledge"
    return f"{entity.name} ({kind}) inferred from {source}."

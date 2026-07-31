"""Default knowledge graph builder with richer relationships for React Flow."""

from __future__ import annotations

from app.services.knowledge.base import (
    GraphEdge,
    GraphNode,
    KnowledgeGraphBuilder,
    KnowledgeGraphData,
    ProjectEntity,
)

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

        def add_node(entity: ProjectEntity) -> None:
            if entity.id in node_ids:
                return
            node_type = entity.entity_type if entity.entity_type in ALLOWED_TYPES else "other"
            nodes.append(
                GraphNode(
                    id=entity.id,
                    label=entity.name,
                    type=node_type,  # type: ignore[arg-type]
                    data={**entity.metadata, "entity_type": entity.entity_type},
                )
            )
            node_ids.add(entity.id)

        def add_edge(source: str, target: str, *, relation: str, label: str | None = None) -> None:
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
        files = [e for e in entities if e.entity_type == "file"]
        techs = [e for e in entities if e.entity_type == "technology"]
        apis = [e for e in entities if e.entity_type == "api"]
        docs = [e for e in entities if e.entity_type == "document"]
        features = [e for e in entities if e.entity_type == "feature"]

        for repo in repo_nodes:
            add_edge(root_id, repo.id, relation="has_repository", label="has repo")

        for module in modules:
            add_edge(root_id, module.id, relation="contains", label="contains")

        for tech in techs:
            add_edge(root_id, tech.id, relation="uses", label="uses")

        for doc in docs:
            add_edge(root_id, doc.id, relation="documented_by", label="documented by")

        for feature in features:
            add_edge(root_id, feature.id, relation="includes", label="includes")

        for file_entity in files:
            parent_module = _matching_module(file_entity.name, modules)
            if parent_module:
                add_edge(parent_module.id, file_entity.id, relation="contains_file", label="file")
            else:
                add_edge(root_id, file_entity.id, relation="contains_file", label="file")

        for api in apis:
            parent_module = _matching_module(api.name, modules)
            if parent_module:
                add_edge(parent_module.id, api.id, relation="exposes", label="exposes")
            else:
                add_edge(root_id, api.id, relation="exposes", label="exposes")

        # Light cross-links for demo richness.
        if techs and modules:
            add_edge(modules[0].id, techs[0].id, relation="implemented_with", label="with")
        if docs and modules:
            add_edge(docs[0].id, modules[0].id, relation="describes", label="describes")

        return KnowledgeGraphData(nodes=nodes, edges=edges)


def _matching_module(path: str, modules: list[ProjectEntity]) -> ProjectEntity | None:
    lower = (path or "").replace("\\", "/").lower()
    for module in modules:
        token = module.name.lower()
        if lower.startswith(f"{token}/") or f"/{token}/" in f"/{lower}/":
            return module
    return None

"""Stub knowledge graph builder for Phase 0 scaffolding."""

from __future__ import annotations

from app.services.knowledge.base import (
    GraphEdge,
    GraphNode,
    KnowledgeGraphBuilder,
    KnowledgeGraphData,
    ProjectEntity,
)


class StubKnowledgeGraphBuilder(KnowledgeGraphBuilder):
    async def build_graph(
        self,
        *,
        project_id: str,
        entities: list[ProjectEntity],
    ) -> KnowledgeGraphData:
        if not entities:
            root_id = f"project:{project_id}"
            return KnowledgeGraphData(
                nodes=[
                    GraphNode(
                        id=root_id,
                        label="Project",
                        type="repository",
                        data={"project_id": project_id},
                    )
                ],
                edges=[],
            )

        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        root_id = f"project:{project_id}"
        nodes.append(
            GraphNode(
                id=root_id,
                label="Project",
                type="repository",
                data={"project_id": project_id},
            )
        )

        for entity in entities:
            node_type = entity.entity_type if entity.entity_type in {
                "file", "module", "technology", "api", "document", "feature", "repository", "other"
            } else "other"
            nodes.append(
                GraphNode(
                    id=entity.id,
                    label=entity.name,
                    type=node_type,  # type: ignore[arg-type]
                    data=entity.metadata,
                )
            )
            edges.append(
                GraphEdge(
                    id=f"{root_id}->{entity.id}",
                    source=root_id,
                    target=entity.id,
                    label="contains",
                    relation="contains",
                )
            )

        return KnowledgeGraphData(nodes=nodes, edges=edges)

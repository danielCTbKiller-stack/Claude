from core.entities import Node, Pipe


class ProjectManager:
    """Gerencia o estado atual do projeto hidrossanitário em memória."""

    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self.pipes: dict[str, Pipe] = {}

    def add_node(self, node: Node):
        self.nodes[node.id] = node

    def add_pipe(self, pipe: Pipe):
        self.pipes[pipe.id] = pipe

    def get_project_summary(self) -> dict:
        return {
            "total_nodes": len(self.nodes),
            "total_pipes": len(self.pipes),
        }

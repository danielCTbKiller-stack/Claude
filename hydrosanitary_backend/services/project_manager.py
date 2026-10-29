from typing import List

from core.entities import Node, Pipe, Room, Wall


class ProjectManager:
    """Gerencia o estado atual do projeto hidrossanitário em memória."""

    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self.pipes: dict[str, Pipe] = {}
        self.walls: List[Wall] = []
        self.rooms: dict[str, Room] = {}

    def add_node(self, node: Node):
        self.nodes[node.id] = node

    def add_pipe(self, pipe: Pipe):
        self.pipes[pipe.id] = pipe

    def add_wall(self, wall: Wall):
        self.walls.append(wall)

    def add_room(self, room: Room):
        self.rooms[room.name] = room

    def get_project_summary(self) -> dict:
        return {
            "total_nodes": len(self.nodes),
            "total_pipes": len(self.pipes),
            "total_rooms": len(self.rooms),
        }

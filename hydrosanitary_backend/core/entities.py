from dataclasses import dataclass, field
from typing import List


@dataclass
class Fixture:
    """Representa um aparelho sanitário (ex: Chuveiro, Bacia, Lavatório)."""
    name: str
    weight: float           # Peso relativo (Método de Hunter)
    min_pressure_mca: float  # Pressão mínima exigida em mca


@dataclass
class Node:
    """Nó hidráulico (conexão, bifurcação ou ponto de consumo)."""
    id: str
    elevation_m: float      # Cota geométrica em relação à referência
    fixtures: List[Fixture] = field(default_factory=list)
    x_m: float = 0.0       # posição em planta (para exibição)
    y_m: float = 0.0


@dataclass
class Pipe:
    """Trecho de tubulação."""
    id: str
    start_node_id: str
    end_node_id: str
    length_m: float
    diameter_mm: float
    material: str = "PVC Soldável"
    equivalent_length_m: float = 0.0  # Comprimento equivalente de conexões

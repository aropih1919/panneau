from dataclasses import dataclass
from typing import Optional

from models.materiel import Materiel


@dataclass(frozen=True)
class MaterielPuissance:
    id: Optional[int]
    materiel: Materiel
    puissance: float

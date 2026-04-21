from dataclasses import dataclass
from datetime import time


@dataclass(frozen=True)
class Tranche:
    id: int
    libelle: str
    heure_debut: time
    heure_fin: time

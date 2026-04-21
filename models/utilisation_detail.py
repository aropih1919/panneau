from dataclasses import dataclass
from datetime import time
from typing import Optional

from models.materiel_puissance import MaterielPuissance
from models.tranche import Tranche


@dataclass(frozen=True)
class UtilisationDetail:
    id: Optional[int]
    materiel_puissance: MaterielPuissance
    tranche: Tranche
    heure_debut: time
    heure_fin: time
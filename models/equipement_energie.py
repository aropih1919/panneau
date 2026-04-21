from dataclasses import dataclass
from typing import Optional

from models.equipement import Equipement


@dataclass
class EquipementEnergie:
    id: Optional[int]
    equipement: Equipement
    grandeur_energetique: Optional[float]
    type_resultat: str = "thrq"
    energie_unitaire: Optional[float] = None
    prix_unitaire: Optional[float] = None
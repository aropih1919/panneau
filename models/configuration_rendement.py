from dataclasses import dataclass

from models.equipement_energie import EquipementEnergie
from models.tranche import Tranche


@dataclass(frozen=True)
class ConfigurationRendement:
    id: int
    tranche: Tranche
    equipement_energie: EquipementEnergie
    taux: float

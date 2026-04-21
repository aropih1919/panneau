from dataclasses import dataclass

from models.equipement_energie import EquipementEnergie


@dataclass(frozen=True)
class ConfigurationPratique:
    id: int
    equipement_energie: EquipementEnergie
    taux: float

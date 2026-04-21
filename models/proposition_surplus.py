from dataclasses import dataclass

from models.equipement_energie import EquipementEnergie


@dataclass(frozen=True)
class PropositionSurplus:
    equipement_energie: EquipementEnergie
    quantite_necessaire: int
    prix_total: float

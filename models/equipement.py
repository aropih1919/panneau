from dataclasses import dataclass


@dataclass(frozen=True)
class Equipement:
    id: int
    libelle: str
    type: str

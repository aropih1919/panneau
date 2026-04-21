from dataclasses import dataclass


@dataclass(frozen=True)
class Materiel:
    id: int
    libelle: str

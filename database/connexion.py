import os
from datetime import time
from typing import Any, Optional

from dotenv import load_dotenv

from models.configuration_pratique import ConfigurationPratique
from models.configuration_rendement import ConfigurationRendement
from models.equipement import Equipement
from models.equipement_energie import EquipementEnergie
from models.materiel import Materiel
from models.materiel_puissance import MaterielPuissance
from models.tranche import Tranche
from models.utilisation_detail import UtilisationDetail

try:
    import pyodbc
except ImportError:
    pyodbc = None


class ConnexionSQLServer:
    """Acces SQL Server pour les donnees de reference."""

    def __init__(self) -> None:
        load_dotenv()
        self._connexion: Optional[Any] = None
        self._driver_utilise: Optional[str] = None
        self._derniere_erreur: Optional[str] = None

    def connecter(self) -> Optional[Any]:
        if pyodbc is None:
            self._derniere_erreur = "Le module pyodbc n'est pas installe."
            return None

        if self._connexion is not None:
            return self._connexion

        server = os.getenv("DB_SERVER", "localhost")
        database = os.getenv("DB_NAME", "equipement_solaire")
        username = os.getenv("DB_USER", "sa")
        password = os.getenv("DB_PASSWORD", "SqlServer123!")
        driver_env = os.getenv("DB_DRIVER", "").strip()

        drivers_installes = [str(d) for d in pyodbc.drivers()]
        candidats: list[str] = []
        if driver_env:
            candidats.append(driver_env)
        for driver in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"):
            if driver not in candidats:
                candidats.append(driver)

        erreurs: list[str] = []
        tentative_faite = False
        for driver in candidats:
            if drivers_installes and driver not in drivers_installes:
                erreurs.append(f"Driver indisponible: {driver}")
                continue

            tentative_faite = True
            chaine = (
                f"DRIVER={{{driver}}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={password};"
                "Encrypt=no;"
                "TrustServerCertificate=yes;"
            )
            try:
                self._connexion = pyodbc.connect(chaine, timeout=3)
                self._driver_utilise = driver
                self._derniere_erreur = None
                return self._connexion
            except Exception as erreur:
                erreurs.append(f"{driver}: {erreur}")

        if not tentative_faite and not drivers_installes:
            self._derniere_erreur = "Aucun driver ODBC detecte sur le systeme."
        else:
            self._derniere_erreur = " | ".join(erreurs) if erreurs else "Connexion SQL Server impossible."
        return None

    def est_connecte(self) -> bool:
        return self.connecter() is not None

    def get_driver_utilise(self) -> Optional[str]:
        return self._driver_utilise

    def get_derniere_erreur(self) -> Optional[str]:
        return self._derniere_erreur

    def _select(self, requete: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
        connexion = self.connecter()
        if connexion is None:
            return []

        try:
            curseur = connexion.cursor()
            curseur.execute(requete, params)
            return list(curseur.fetchall())
        except Exception as erreur:
            self._derniere_erreur = str(erreur)
            return []

    def _execute(self, requete: str, params: tuple[Any, ...] = ()) -> bool:
        connexion = self.connecter()
        if connexion is None:
            return False

        try:
            curseur = connexion.cursor()
            curseur.execute(requete, params)
            connexion.commit()
            return True
        except Exception as erreur:
            self._derniere_erreur = str(erreur)
            try:
                connexion.rollback()
            except Exception:
                pass
            return False

    def _insert_returning_id(self, requete: str, params: tuple[Any, ...] = ()) -> Optional[int]:
        connexion = self.connecter()
        if connexion is None:
            return None

        try:
            curseur = connexion.cursor()
            curseur.execute(requete, params)
            ligne = curseur.fetchone()
            connexion.commit()
            if ligne is None:
                return None
            return int(ligne[0])
        except Exception as erreur:
            self._derniere_erreur = str(erreur)
            try:
                connexion.rollback()
            except Exception:
                pass
            return None

    def charger_materiels(self) -> list[Materiel]:
        lignes = self._select(
            """
            SELECT id, libelle
            FROM Materiel
            ORDER BY libelle
            """
        )
        return [Materiel(id=int(l.id), libelle=str(l.libelle)) for l in lignes]

    def charger_tranches(self) -> list[Tranche]:
        lignes = self._select(
            """
            SELECT id, libelle, HeureDebut, HeureFin
            FROM Tranche
            ORDER BY id
            """
        )
        tranches: list[Tranche] = []
        for ligne in lignes:
            tranches.append(
                Tranche(
                    id=int(ligne.id),
                    libelle=str(ligne.libelle),
                    heure_debut=self._vers_time(ligne.HeureDebut),
                    heure_fin=self._vers_time(ligne.HeureFin),
                )
            )
        return tranches

    def charger_equipements(self) -> list[Equipement]:
        lignes = self._select(
            """
            SELECT id, libelle, type
            FROM Equipement
            ORDER BY libelle
            """
        )
        return [
            Equipement(
                id=int(l.id),
                libelle=str(l.libelle),
                type=str(l.type),
            )
            for l in lignes
        ]

    def charger_utilisations_details(self, materiels: list[Materiel], tranches: list[Tranche]) -> list[UtilisationDetail]:
        lignes = self._select(
            """
            SELECT
                ud.id,
                ud.HeureDebut,
                ud.HeureFin,
                mp.id AS mp_id,
                mp.puissance,
                m.id AS m_id,
                t.id AS t_id
            FROM UtilisationDetail ud
            INNER JOIN MaterielPuissance mp ON mp.id = ud.idMaterielPuissance
            INNER JOIN Materiel m ON m.id = mp.idMaterielle
            INNER JOIN Tranche t ON t.id = ud.idTranche
            ORDER BY ud.id
            """
        )

        materiel_par_id = {m.id: m for m in materiels}
        tranche_par_id = {t.id: t for t in tranches}
        details: list[UtilisationDetail] = []

        for ligne in lignes:
            materiel = materiel_par_id.get(int(ligne.m_id))
            tranche = tranche_par_id.get(int(ligne.t_id))
            if materiel is None or tranche is None:
                continue

            details.append(
                UtilisationDetail(
                    id=int(ligne.id),
                    materiel_puissance=MaterielPuissance(
                        id=int(ligne.mp_id),
                        materiel=materiel,
                        puissance=float(ligne.puissance),
                    ),
                    tranche=tranche,
                    heure_debut=self._vers_time(ligne.HeureDebut),
                    heure_fin=self._vers_time(ligne.HeureFin),
                )
            )

        return details

    def charger_equipements_energie(self, equipements: list[Equipement]) -> list[EquipementEnergie]:
        lignes = self._select(
            """
            SELECT
                ee.id,
                ee.idEquipement,
                ee.grandeurEnergetique,
                ee.type,
                c.energieUnitaire,
                c.prixUnitaire
            FROM EquipementEnergie ee
            LEFT JOIN EquipementEnergieCaracteristique c ON c.idEquipementEnergie = ee.id
            ORDER BY ee.id
            """
        )

        equipement_par_id = {e.id: e for e in equipements}
        references: list[EquipementEnergie] = []
        for ligne in lignes:
            equipement = equipement_par_id.get(int(ligne.idEquipement))
            if equipement is None:
                continue
            references.append(self._construire_equipement_energie(ligne, equipement))
        return references

    def charger_configurations_rendement(self, tranches: list[Tranche], equipements: list[Equipement]) -> list[ConfigurationRendement]:
        lignes = self._select(
            """
            SELECT
                cr.id,
                cr.idTranche,
                cr.taux,
                ee.id AS ee_id,
                ee.grandeurEnergetique,
                ee.type AS ee_type,
                c.energieUnitaire AS ee_energie_unitaire,
                c.prixUnitaire AS ee_prix_unitaire,
                e.id AS e_id,
                e.libelle,
                e.type
            FROM ConfigurationRendement cr
            INNER JOIN EquipementEnergie ee ON ee.id = cr.idEquipementEnergie
            INNER JOIN Equipement e ON e.id = ee.idEquipement
            LEFT JOIN EquipementEnergieCaracteristique c ON c.idEquipementEnergie = ee.id
            ORDER BY cr.id
            """
        )

        tranche_par_id = {t.id: t for t in tranches}
        equipement_par_id = {e.id: e for e in equipements}
        configurations: list[ConfigurationRendement] = []

        for l in lignes:
            tranche = tranche_par_id.get(int(l.idTranche))
            equipement = equipement_par_id.get(int(l.e_id))
            if tranche is None or equipement is None:
                continue

            ee = self._construire_equipement_energie(l, equipement)
            configurations.append(
                ConfigurationRendement(
                    id=int(l.id),
                    tranche=tranche,
                    equipement_energie=ee,
                    taux=float(l.taux),
                )
            )

        return configurations

    def charger_configurations_pratiques(self, equipements: list[Equipement]) -> list[ConfigurationPratique]:
        lignes = self._select(
            """
            SELECT
                cp.id,
                cp.taux,
                ee.id AS ee_id,
                ee.grandeurEnergetique,
                ee.type AS ee_type,
                c.energieUnitaire AS ee_energie_unitaire,
                c.prixUnitaire AS ee_prix_unitaire,
                e.id AS e_id,
                e.libelle,
                e.type
            FROM ConfigurationPratique cp
            INNER JOIN EquipementEnergie ee ON ee.id = cp.idEquipementEnergie
            INNER JOIN Equipement e ON e.id = ee.idEquipement
            LEFT JOIN EquipementEnergieCaracteristique c ON c.idEquipementEnergie = ee.id
            ORDER BY cp.id
            """
        )

        equipement_par_id = {e.id: e for e in equipements}
        configurations: list[ConfigurationPratique] = []
        for ligne in lignes:
            equipement = equipement_par_id.get(int(ligne.e_id))
            if equipement is None:
                continue
            ee = self._construire_equipement_energie(ligne, equipement)
            configurations.append(
                ConfigurationPratique(
                    id=int(ligne.id),
                    equipement_energie=ee,
                    taux=float(ligne.taux),
                )
            )

        return configurations

    def assurer_equipement_energie_reference(self, equipement: Equipement) -> Optional[EquipementEnergie]:
        lignes = self._select(
            """
            SELECT TOP 1
                ee.id,
                ee.idEquipement,
                ee.grandeurEnergetique,
                ee.type,
                c.energieUnitaire,
                c.prixUnitaire
            FROM EquipementEnergie ee
            LEFT JOIN EquipementEnergieCaracteristique c ON c.idEquipementEnergie = ee.id
            WHERE ee.idEquipement = ?
            ORDER BY CASE WHEN LOWER(ee.type) = 'thrq' THEN 0 ELSE 1 END, ee.id
            """,
            (equipement.id,),
        )
        if lignes:
            return self._construire_equipement_energie(lignes[0], equipement)

        succes = self._execute(
            """
            INSERT INTO EquipementEnergie (idEquipement, grandeurEnergetique, type)
            VALUES (?, NULL, 'thrq')
            """,
            (equipement.id,),
        )
        if not succes:
            return None

        lignes = self._select(
            """
            SELECT TOP 1
                ee.id,
                ee.idEquipement,
                ee.grandeurEnergetique,
                ee.type,
                c.energieUnitaire,
                c.prixUnitaire
            FROM EquipementEnergie ee
            LEFT JOIN EquipementEnergieCaracteristique c ON c.idEquipementEnergie = ee.id
            WHERE ee.idEquipement = ?
            ORDER BY ee.id DESC
            """,
            (equipement.id,),
        )
        if not lignes:
            return None
        return self._construire_equipement_energie(lignes[0], equipement)

    def creer_equipement_energie_reference(self, equipement: Equipement) -> Optional[EquipementEnergie]:
        nouvel_id = self._insert_returning_id(
            """
            INSERT INTO EquipementEnergie (idEquipement, grandeurEnergetique, type)
            OUTPUT INSERTED.id
            VALUES (?, NULL, 'thrq')
            """,
            (equipement.id,),
        )
        if nouvel_id is None:
            return None
        return EquipementEnergie(
            id=nouvel_id,
            equipement=equipement,
            grandeur_energetique=None,
            type_resultat="thrq",
        )

    def upsert_configuration_pratique(self, equipement_energie_id: int, taux: float) -> bool:
        return self._execute(
            """
            IF EXISTS (
                SELECT 1
                FROM ConfigurationPratique
                WHERE idEquipementEnergie = ?
            )
            BEGIN
                UPDATE ConfigurationPratique
                SET taux = ?
                WHERE idEquipementEnergie = ?
            END
            ELSE
            BEGIN
                INSERT INTO ConfigurationPratique (idEquipementEnergie, taux)
                VALUES (?, ?)
            END
            """,
            (equipement_energie_id, taux, equipement_energie_id, equipement_energie_id, taux),
        )

    def upsert_equipement_energie_caracteristique(
        self,
        equipement_energie_id: int,
        energie_unitaire: float,
        prix_unitaire: float,
    ) -> bool:
        return self._execute(
            """
            IF EXISTS (
                SELECT 1
                FROM EquipementEnergieCaracteristique
                WHERE idEquipementEnergie = ?
            )
            BEGIN
                UPDATE EquipementEnergieCaracteristique
                SET energieUnitaire = ?, prixUnitaire = ?
                WHERE idEquipementEnergie = ?
            END
            ELSE
            BEGIN
                INSERT INTO EquipementEnergieCaracteristique (idEquipementEnergie, energieUnitaire, prixUnitaire)
                VALUES (?, ?, ?)
            END
            """,
            (
                equipement_energie_id,
                energie_unitaire,
                prix_unitaire,
                equipement_energie_id,
                equipement_energie_id,
                energie_unitaire,
                prix_unitaire,
            ),
        )

    @staticmethod
    def _construire_equipement_energie(ligne: Any, equipement: Equipement) -> EquipementEnergie:
        energie_unitaire = getattr(ligne, "ee_energie_unitaire", getattr(ligne, "energieUnitaire", None))
        prix_unitaire = getattr(ligne, "ee_prix_unitaire", getattr(ligne, "prixUnitaire", None))
        type_resultat = getattr(ligne, "ee_type", getattr(ligne, "type", "thrq"))
        return EquipementEnergie(
            id=int(getattr(ligne, "ee_id", getattr(ligne, "id"))),
            equipement=equipement,
            grandeur_energetique=(
                float(getattr(ligne, "grandeurEnergetique"))
                if getattr(ligne, "grandeurEnergetique") is not None
                else None
            ),
            type_resultat=str(type_resultat),
            energie_unitaire=float(energie_unitaire) if energie_unitaire is not None else None,
            prix_unitaire=float(prix_unitaire) if prix_unitaire is not None else None,
        )

    @staticmethod
    def _vers_time(valeur: Any) -> time:
        if isinstance(valeur, time):
            return valeur

        texte = str(valeur)
        morceaux = texte.split(":")
        heure = int(morceaux[0])
        minute = int(morceaux[1])
        seconde = int(morceaux[2]) if len(morceaux) > 2 else 0
        return time(hour=heure, minute=minute, second=seconde)

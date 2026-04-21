from copy import deepcopy
from datetime import datetime, time, timedelta
import math

from models.configuration_pratique import ConfigurationPratique
from database.connexion import ConnexionSQLServer
from models.configuration_rendement import ConfigurationRendement
from models.equipement import Equipement
from models.equipement_energie import EquipementEnergie
from models.materiel import Materiel
from models.materiel_puissance import MaterielPuissance
from models.proposition_surplus import PropositionSurplus
from models.tranche import Tranche
from models.utilisation_detail import UtilisationDetail


class MonController:
    def __init__(self) -> None:
        self.db = ConnexionSQLServer()
        self._references_depuis_db = False
        self._materiels: list[Materiel] = []
        self._tranches: list[Tranche] = []
        self._equipements: list[Equipement] = []
        self._utilisations_details: list[UtilisationDetail] = []
        self._equipements_energie_reference: list[EquipementEnergie] = []
        self._configurations_rendement: list[ConfigurationRendement] = []
        self._configurations_pratiques: list[ConfigurationPratique] = []

        self.utilisations_en_attente: list[UtilisationDetail] = []
        self.equipements_energie_en_attente: list[EquipementEnergie] = []

        self._charger_references()

    def _charger_references(self) -> None:
        materiels_db = self.db.charger_materiels()
        tranches_db = self.db.charger_tranches()
        equipements_db = self.db.charger_equipements()
        self._materiels = materiels_db
        self._tranches = tranches_db
        self._equipements = equipements_db
        self._references_depuis_db = bool(materiels_db and tranches_db and equipements_db)
        if self._materiels and self._tranches:
            self._utilisations_details = self.db.charger_utilisations_details(self._materiels, self._tranches)
            self.utilisations_en_attente = list(self._utilisations_details)
        else:
            self._utilisations_details = []
            self.utilisations_en_attente = []

        if self._equipements:
            self._equipements_energie_reference = self.db.charger_equipements_energie(self._equipements)
            self._configurations_pratiques = self.db.charger_configurations_pratiques(self._equipements)
        else:
            self._equipements_energie_reference = []
            self._configurations_pratiques = []

        if self._tranches and self._equipements:
            self._configurations_rendement = self.db.charger_configurations_rendement(self._tranches, self._equipements)
        else:
            self._configurations_rendement = []

    def verifier_systeme(self) -> str:
        if self._references_depuis_db:
            driver = self.db.get_driver_utilise()
            if driver:
                return (
                    "Base connectee: references Materiel/Tranche/Equipement et UtilisationDetail chargees "
                    f"depuis SQL Server (driver: {driver})."
                )
            return "Base connectee: references Materiel/Tranche/Equipement et UtilisationDetail chargees depuis SQL Server."
        if self.db.est_connecte():
            return "Base connectee mais references introuvables dans les tables."
        erreur = self.db.get_derniere_erreur()
        if erreur:
            return f"Base non connectee: aucune reference chargee. Detail: {erreur}"
        return "Base non connectee: aucune reference chargee."

    def get_materiels(self) -> list[Materiel]:
        return list(self._materiels)

    def get_tranches(self) -> list[Tranche]:
        return list(self._tranches)

    def get_equipements(self) -> list[Equipement]:
        return list(self._equipements)

    def get_utilisations_details(self) -> list[UtilisationDetail]:
        return list(self._utilisations_details)

    def creer_utilisation_detail(
        self,
        materiel_id: int,
        tranche_id: int,
        heure_debut_txt: str,
        heure_fin_txt: str,
        puissance_txt: str,
    ) -> UtilisationDetail:
        materiel = self._trouver_materiel(materiel_id)
        tranche = self._trouver_tranche(tranche_id)
        heure_debut = self._parse_horaire(heure_debut_txt)
        heure_fin = self._parse_horaire(heure_fin_txt)
        puissance = float(puissance_txt)

        materiel_puissance = MaterielPuissance(
            id=None,
            materiel=materiel,
            puissance=puissance,
        )

        return UtilisationDetail(
            id=None,
            materiel_puissance=materiel_puissance,
            tranche=tranche,
            heure_debut=heure_debut,
            heure_fin=heure_fin,
        )

    def definir_utilisations_en_attente(self, details: list[UtilisationDetail]) -> None:
        self.utilisations_en_attente = list(details)

    def creer_equipements_energie_depuis_equipements(self, equipement_ids: list[int]) -> list[EquipementEnergie]:
        selection: list[EquipementEnergie] = []
        deja_vus: set[int] = set()

        for equipement_id in equipement_ids:
            if equipement_id in deja_vus:
                continue
            equipement = self._trouver_equipement(equipement_id)
            reference = self._trouver_equipement_energie_reference_disponible(equipement_id, selection)
            selection.append(
                EquipementEnergie(
                    id=reference.id if reference is not None else None,
                    equipement=equipement,
                    grandeur_energetique=None,
                    type_resultat="thrq",
                    energie_unitaire=reference.energie_unitaire if reference is not None else None,
                    prix_unitaire=reference.prix_unitaire if reference is not None else None,
                )
            )
            deja_vus.add(equipement_id)

        self.equipements_energie_en_attente = selection
        return list(selection)

    def synchroniser_configurations_pratiques(
        self,
        taux_par_equipement: dict[int, float],
    ) -> tuple[list[EquipementEnergie], list[ConfigurationPratique]]:
        selection: list[EquipementEnergie] = []
        configurations: list[ConfigurationPratique] = []

        for equipement_id, taux in taux_par_equipement.items():
            equipement = self._trouver_equipement(equipement_id)
            reference = self.db.assurer_equipement_energie_reference(equipement)
            if reference is None or reference.id is None:
                raise ValueError(f"Impossible de preparer EquipementEnergie pour {equipement.libelle}.")
            if not self.db.upsert_configuration_pratique(reference.id, taux):
                detail = self.db.get_derniere_erreur() or "insertion SQL Server impossible"
                raise ValueError(f"ConfigurationPratique impossible pour {equipement.libelle}: {detail}")

            selection.append(reference)
            configurations.append(
                ConfigurationPratique(
                    id=0,
                    equipement_energie=reference,
                    taux=taux,
                )
            )

        self._charger_references()

        ee_par_equipement = {
            ee.equipement.id: ee
            for ee in self._equipements_energie_reference
            if ee.id is not None
        }
        configurations_chargees = self.db.charger_configurations_pratiques(self._equipements)
        cfg_par_equipement = {
            cfg.equipement_energie.equipement.id: cfg
            for cfg in configurations_chargees
        }

        selection_finale: list[EquipementEnergie] = []
        configurations_finales: list[ConfigurationPratique] = []
        for equipement_id in taux_par_equipement:
            ee = ee_par_equipement.get(equipement_id)
            if ee is not None:
                selection_finale.append(deepcopy(ee))
            cfg = cfg_par_equipement.get(equipement_id)
            if cfg is not None:
                configurations_finales.append(cfg)

        self.equipements_energie_en_attente = selection_finale
        self._configurations_pratiques = configurations_chargees
        return selection_finale, configurations_finales

    def enregistrer_equipements_selectionnes(
        self,
        selections: list[dict[str, float | int]],
    ) -> tuple[list[EquipementEnergie], list[ConfigurationPratique]]:
        selection_finale: list[EquipementEnergie] = []

        for element in selections:
            equipement_id = int(element["equipement_id"])
            taux = float(element["taux"])
            equipement = self._trouver_equipement(equipement_id)
            type_equipement = equipement.type.strip().lower()

            if type_equipement == "ps":
                nombre = int(element["nombre"])
                energie_unitaire = float(element["energie_unitaire"])
                prix_unitaire = float(element["prix_unitaire"])

                for _ in range(nombre):
                    reference = self.db.creer_equipement_energie_reference(equipement)
                    if reference is None or reference.id is None:
                        raise ValueError(f"Impossible de creer un panneau {equipement.libelle}.")
                    if not self.db.upsert_configuration_pratique(reference.id, taux):
                        detail = self.db.get_derniere_erreur() or "insertion SQL Server impossible"
                        raise ValueError(f"ConfigurationPratique impossible pour {equipement.libelle}: {detail}")
                    if not self.db.upsert_equipement_energie_caracteristique(reference.id, energie_unitaire, prix_unitaire):
                        detail = self.db.get_derniere_erreur() or "insertion SQL Server impossible"
                        raise ValueError(f"Caracteristique impossible pour {equipement.libelle}: {detail}")

                    reference.energie_unitaire = energie_unitaire
                    reference.prix_unitaire = prix_unitaire
                    selection_finale.append(reference)
            else:
                reference = self.db.assurer_equipement_energie_reference(equipement)
                if reference is None or reference.id is None:
                    raise ValueError(f"Impossible de preparer EquipementEnergie pour {equipement.libelle}.")
                if not self.db.upsert_configuration_pratique(reference.id, taux):
                    detail = self.db.get_derniere_erreur() or "insertion SQL Server impossible"
                    raise ValueError(f"ConfigurationPratique impossible pour {equipement.libelle}: {detail}")
                selection_finale.append(reference)

        self._charger_references()

        ids_selectionnes = {ee.id for ee in selection_finale if ee.id is not None}
        selection_chargee = [
            deepcopy(ee)
            for ee in self._equipements_energie_reference
            if ee.id in ids_selectionnes
        ]
        configurations_chargees = [
            cfg
            for cfg in self._configurations_pratiques
            if cfg.equipement_energie.id in ids_selectionnes
        ]

        self.equipements_energie_en_attente = selection_chargee
        return selection_chargee, configurations_chargees

    def filtrerUtilsationDSelonEquipementE(
        self,
        lud: list[UtilisationDetail],
        ee: EquipementEnergie,
    ) -> list[UtilisationDetail]:
        resultat: list[UtilisationDetail] = []
        type_equipement = ee.equipement.type.strip().lower()

        if type_equipement != "btr":
            for detail in lud:
                if detail.tranche.libelle.strip().lower() != "alina":
                    resultat.append(deepcopy(detail))
            return resultat

        for detail in lud:
            if detail.tranche.libelle.strip().lower() == "alina":
                resultat.append(deepcopy(detail))
        return resultat

    def filtrerUtilisationDSelonEquipementE(
        self,
        lud: list[UtilisationDetail],
        ee: EquipementEnergie,
    ) -> list[UtilisationDetail]:
        return self.filtrerUtilsationDSelonEquipementE(lud, ee)

    def calculMultiplicative(self, lud: list[UtilisationDetail], ee: EquipementEnergie) -> None:
        type_equipement = ee.equipement.type.strip().lower()
        if type_equipement != "btr":
            return

        energie_totale = 0.0
        for detail in lud:
            duree_heure = self._duree_heure(detail.heure_debut, detail.heure_fin)
            energie_totale += detail.materiel_puissance.puissance * duree_heure

        ee.grandeur_energetique = energie_totale

    def caclulMaxAdditive(self, lud: list[UtilisationDetail]) -> float:
        maraina: list[UtilisationDetail] = []
        hariva: list[UtilisationDetail] = []

        for detail in lud:
            libelle = detail.tranche.libelle.strip().lower()
            if libelle == "am":
                maraina.append(deepcopy(detail))
            elif libelle == "hariva":
                hariva.append(deepcopy(detail))

        cmaraina = self._trouver_configuration_par_tranche_et_type_equipement("AM", "ps")
        chariva = self._trouver_configuration_par_tranche_et_type_equipement("Hariva", "ps")

        if cmaraina is None or chariva is None:
            raise ValueError("ConfigurationRendement manquante pour AM/Hariva.")

        puissance_maraina = self._puissance_max_simultanee(maraina)
        puissance_hariva = self._puissance_max_simultanee(hariva)

        puissance_evaluer = 0.0
        if cmaraina.taux >= chariva.taux:
            puissance_evaluer = puissance_hariva * 100.0 / chariva.taux if chariva.taux > 0 else 0.0
            if puissance_evaluer < puissance_maraina:
                puissance_evaluer = puissance_maraina
        else:
            puissance_evaluer = puissance_maraina * 100.0 / cmaraina.taux if cmaraina.taux > 0 else 0.0
            if puissance_evaluer < puissance_hariva:
                puissance_evaluer = puissance_hariva

        return puissance_evaluer

    def calculMaxAdditive(self, lud: list[UtilisationDetail]) -> float:
        return self.caclulMaxAdditive(lud)

    def caclulMaxAdditiveAutre(self, lud: list[UtilisationDetail], ee: EquipementEnergie) -> None:
        puissance = self.caclulMaxAdditive(lud)
        puissance_reel = puissance * 2
        ee.grandeur_energetique = puissance_reel

    def calcBatterieMinim(self, ee: EquipementEnergie) -> float:
        cmaraina = self._trouver_configuration_par_tranche_et_type_equipement("AM", "ps")
        chariva = self._trouver_configuration_par_tranche_et_type_equipement("Hariva", "ps")
        if cmaraina is None or chariva is None:
            raise ValueError("ConfigurationRendement manquante pour AM/Hariva.")

        dmaraina = self._duree_heure(cmaraina.tranche.heure_debut, cmaraina.tranche.heure_fin)
        dhariva = self._duree_heure(chariva.tranche.heure_debut, chariva.tranche.heure_fin)

        energie_batterie = ee.grandeur_energetique or 0.0
        denom = dmaraina * cmaraina.taux / 100.0 + dhariva * chariva.taux / 100.0
        if denom <= 0:
            return 0.0
        return energie_batterie / denom

    def caclulMaxAdditiveSurplus(
        self,
        lud: list[UtilisationDetail],
        ee: EquipementEnergie,
        le: list[EquipementEnergie],
    ) -> None:
        puissance = self.caclulMaxAdditive(lud)
        puissance_batterie = 0.0

        for element in le:
            if element.equipement.type.strip().lower() == "btr":
                puissance_batterie = self.calcBatterieMinim(element)
                break

        ee.grandeur_energetique = puissance + puissance_batterie

    def ProposerTheorique(
        self,
        lud: list[UtilisationDetail],
        le: list[EquipementEnergie],
    ) -> list[EquipementEnergie]:
        if not lud:
            raise ValueError("Aucune utilisation detail a evaluer.")
        if not le:
            raise ValueError("Aucun equipement energie selectionne.")

        liste_reordonnee = sorted(
            [deepcopy(e) for e in le],
            key=lambda e: 0 if e.equipement.type.strip().lower() == "btr" else 1,
        )

        for equipement_energie in liste_reordonnee:
            tempo = self.filtrerUtilsationDSelonEquipementE(lud, equipement_energie)
            type_equipement = equipement_energie.equipement.type.strip().lower()

            if type_equipement == "btr":
                self.calculMultiplicative(tempo, equipement_energie)
            elif type_equipement == "ps":
                self.caclulMaxAdditiveSurplus(tempo, equipement_energie, liste_reordonnee)
            else:
                self.caclulMaxAdditiveAutre(tempo, equipement_energie)

        self.equipements_energie_en_attente = liste_reordonnee
        return list(liste_reordonnee)

    def proposerPratique(
        self,
        ee: EquipementEnergie,
        lc: list[ConfigurationPratique],
    ) -> EquipementEnergie:
        resultat = EquipementEnergie(
            id=None,
            equipement=deepcopy(ee.equipement),
            grandeur_energetique=ee.grandeur_energetique,
            type_resultat="prtq",
            energie_unitaire=ee.energie_unitaire,
            prix_unitaire=ee.prix_unitaire,
        )

        configuration = None
        for element in lc:
            if ee.id is not None and element.equipement_energie.id == ee.id:
                configuration = element
                break
            if element.equipement_energie.equipement.id == ee.equipement.id:
                configuration = element

        if configuration is None or ee.grandeur_energetique is None:
            return resultat

        type_equipement = ee.equipement.type.strip().lower()
        if type_equipement == "btr":
            energie = ee.grandeur_energetique * (1 + configuration.taux / 100.0)
            resultat.grandeur_energetique = energie
        elif type_equipement == "ps" and configuration.taux != 0:
            energie = ee.grandeur_energetique * 100.0 / configuration.taux
            resultat.grandeur_energetique = energie

        return resultat

    def calculer_propositions_surplus(self, besoins_pratiques: list[EquipementEnergie]) -> list[PropositionSurplus]:
        propositions: list[PropositionSurplus] = []

        for equipement_energie in besoins_pratiques:
            if equipement_energie.equipement.type.strip().lower() != "ps":
                continue
            if equipement_energie.grandeur_energetique is None:
                continue
            if not equipement_energie.energie_unitaire or not equipement_energie.prix_unitaire:
                continue

            quantite = math.ceil(equipement_energie.grandeur_energetique / equipement_energie.energie_unitaire)
            prix_total = quantite * equipement_energie.prix_unitaire
            propositions.append(
                PropositionSurplus(
                    equipement_energie=deepcopy(equipement_energie),
                    quantite_necessaire=quantite,
                    prix_total=prix_total,
                )
            )

        propositions.sort(key=lambda item: (item.prix_total, item.quantite_necessaire, item.equipement_energie.equipement.libelle))
        return propositions

    def proposerEnsemble(
        self,
        lud: list[UtilisationDetail],
        le_theorique: list[EquipementEnergie],
        le_pratique: list[EquipementEnergie],
    ) -> tuple[list[EquipementEnergie], list[EquipementEnergie], list[PropositionSurplus], PropositionSurplus | None]:
        resultats_theoriques = self.ProposerTheorique(lud, le_theorique)
        configurations_pratiques = list(self._configurations_pratiques)

        le_pratique.clear()
        for equipement_energie in resultats_theoriques:
            le_pratique.append(self.proposerPratique(equipement_energie, configurations_pratiques))

        propositions = self.calculer_propositions_surplus(le_pratique)
        meilleure = propositions[0] if propositions else None

        return list(resultats_theoriques), list(le_pratique), propositions, meilleure

    def _trouver_materiel(self, materiel_id: int) -> Materiel:
        for item in self._materiels:
            if item.id == materiel_id:
                return item
        raise ValueError("Materiel introuvable.")

    def _trouver_tranche(self, tranche_id: int) -> Tranche:
        for item in self._tranches:
            if item.id == tranche_id:
                return item
        raise ValueError("Tranche introuvable.")

    def _trouver_equipement(self, equipement_id: int) -> Equipement:
        for item in self._equipements:
            if item.id == equipement_id:
                return item
        raise ValueError("Equipement introuvable.")

    def _trouver_tranche_par_libelle(self, libelle: str) -> Tranche | None:
        cible = libelle.strip().lower()
        for tranche in self._tranches:
            if tranche.libelle.strip().lower() == cible:
                return tranche
        return None

    def _premier_equipement_par_type(self, type_equipement: str) -> Equipement | None:
        cible = type_equipement.strip().lower()
        for equipement in self._equipements:
            if equipement.type.strip().lower() == cible:
                return equipement
        return None

    def _trouver_equipement_energie_reference_disponible(
        self,
        equipement_id: int,
        selection: list[EquipementEnergie],
    ) -> EquipementEnergie | None:
        ids_selectionnes = {item.id for item in selection if item.id is not None}
        for reference in self._equipements_energie_reference:
            if reference.equipement.id == equipement_id and reference.id not in ids_selectionnes:
                return reference
        for reference in self._equipements_energie_reference:
            if reference.equipement.id == equipement_id:
                return reference
        return None

    def _trouver_configuration_par_tranche(self, libelle_tranche: str) -> ConfigurationRendement | None:
        cible = libelle_tranche.strip().lower()
        for cfg in self._configurations_rendement:
            if cfg.tranche.libelle.strip().lower() == cible:
                return cfg
        return None

    def _trouver_configuration_par_tranche_et_type_equipement(
        self,
        libelle_tranche: str,
        type_equipement: str,
    ) -> ConfigurationRendement | None:
        cible_tranche = libelle_tranche.strip().lower()
        cible_type = type_equipement.strip().lower()
        for cfg in self._configurations_rendement:
            if cfg.tranche.libelle.strip().lower() != cible_tranche:
                continue
            if cfg.equipement_energie.equipement.type.strip().lower() != cible_type:
                continue
            return cfg
        return None

    @staticmethod
    def _parse_horaire(valeur: str) -> time:
        texte = valeur.strip()
        morceaux = texte.split(":")
        if len(morceaux) != 2:
            raise ValueError("Format horaire invalide. Utilisez HH:MM.")

        heure = int(morceaux[0])
        minute = int(morceaux[1])
        if heure < 0 or heure > 23 or minute < 0 or minute > 59:
            raise ValueError("Horaire hors intervalle valide.")
        return time(hour=heure, minute=minute)

    @staticmethod
    def _duree_heure(heure_debut: time, heure_fin: time) -> float:
        debut = datetime.combine(datetime.today(), heure_debut)
        fin = datetime.combine(datetime.today(), heure_fin)
        if fin < debut:
            fin = fin + timedelta(days=1)
        return (fin - debut).total_seconds() / 3600.0

    @staticmethod
    def _puissance_max_simultanee(details: list[UtilisationDetail]) -> float:
        evenements: list[tuple[int, float]] = []
        for detail in details:
            debut_sec = detail.heure_debut.hour * 3600 + detail.heure_debut.minute * 60 + detail.heure_debut.second
            fin_sec = detail.heure_fin.hour * 3600 + detail.heure_fin.minute * 60 + detail.heure_fin.second
            if fin_sec < debut_sec:
                fin_sec += 24 * 3600
            puissance = detail.materiel_puissance.puissance
            evenements.append((debut_sec, puissance))
            evenements.append((fin_sec, -puissance))

        evenements.sort(key=lambda e: (e[0], 0 if e[1] < 0 else 1))

        courant = 0.0
        maximum = 0.0
        for _, variation in evenements:
            courant += variation
            if courant > maximum:
                maximum = courant

        return maximum

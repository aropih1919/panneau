import tkinter as tk
from tkinter import messagebox, ttk

from controllers.mon_controller import MonController
from models.equipement import Equipement
from models.equipement_energie import EquipementEnergie
from models.utilisation_detail import UtilisationDetail
from views.fenetre_besoins_theoriques import FenetreBesoinsTheoriques


class FenetreFormulaire(tk.Toplevel):
    def __init__(self, parent: tk.Tk, controller: MonController) -> None:
        super().__init__(parent)
        self.controller = controller

        self.title("Scenario 1 - Donnees depuis la base")
        self.geometry("1120x720")
        self.minsize(980, 620)
        self.configure(bg="#eef2f5")

        self.utilisations_locales: list[UtilisationDetail] = self.controller.get_utilisations_details()
        self.equipements = self.controller.get_equipements()
        self.equipements_energie_locaux: list[EquipementEnergie] = []
        self._taux_pratiques_par_equipement: dict[int, float] = {}
        self._selection_equipements: list[dict[str, float | int]] = []

        self._initialiser_style()
        self._construire_vue()
        self._charger_donnees_utilisation()

    def _initialiser_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Panel.TFrame", background="#ffffff")
        style.configure("TitreForm.TLabel", font=("Segoe UI", 15, "bold"), background="#ffffff", foreground="#1f2d3d")
        style.configure("SousTitreForm.TLabel", font=("Segoe UI", 11, "bold"), background="#ffffff", foreground="#2b3a4a")
        style.configure("Form.TLabel", font=("Segoe UI", 10), background="#ffffff", foreground="#1f2d3d")
        style.configure("Hint.TLabel", font=("Segoe UI", 9), background="#ffffff", foreground="#6b7a88")
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=7)

    def _construire_vue(self) -> None:
        wrapper = ttk.Frame(self, style="Panel.TFrame", padding=20)
        wrapper.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.95, relheight=0.93)

        ttk.Label(wrapper, text="Scenario 1 - UtilisationDetail depuis la base", style="TitreForm.TLabel").pack(anchor="w", pady=(0, 8))
        ttk.Label(
            wrapper,
            text="Les utilisations ci-dessous sont chargees directement depuis SQL Server. Les calculs suivants partent de ces donnees.",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(0, 12))

        colonnes = ("materiel", "tranche", "heure_debut", "heure_fin", "puissance")
        self.table = ttk.Treeview(wrapper, columns=colonnes, show="headings", height=10)
        self.table.heading("materiel", text="Materiel")
        self.table.heading("tranche", text="Tranche")
        self.table.heading("heure_debut", text="Heure debut")
        self.table.heading("heure_fin", text="Heure fin")
        self.table.heading("puissance", text="Puissance (W)")
        self.table.column("materiel", width=245)
        self.table.column("tranche", width=180)
        self.table.column("heure_debut", width=110, anchor="center")
        self.table.column("heure_fin", width=110, anchor="center")
        self.table.column("puissance", width=120, anchor="e")
        self.table.pack(fill="both", expand=True)

        ttk.Separator(wrapper, orient="horizontal").pack(fill="x", pady=14)
        ttk.Label(wrapper, text="Selection multiple des equipements", style="SousTitreForm.TLabel").pack(anchor="w", pady=(0, 8))

        equip_zone = ttk.Frame(wrapper, style="Panel.TFrame")
        equip_zone.pack(fill="x")

        gauche = ttk.Frame(equip_zone, style="Panel.TFrame")
        gauche.pack(side="left", fill="both", expand=True)
        ttk.Label(gauche, text="Equipements disponibles", style="Form.TLabel").pack(anchor="w", pady=(0, 4))

        self.equipements_listbox = tk.Listbox(
            gauche,
            selectmode=tk.MULTIPLE,
            height=6,
            exportselection=False,
            bg="#ffffff",
            fg="#1f2d3d",
            font=("Segoe UI", 10),
            relief="solid",
            borderwidth=1,
        )
        self.equipements_listbox.pack(fill="x", expand=True, padx=(0, 12))
        for equipement in self.equipements:
            self.equipements_listbox.insert(tk.END, self._label_equipement(equipement))

        droite = ttk.Frame(equip_zone, style="Panel.TFrame")
        droite.pack(side="left", fill="both", expand=True)
        ttk.Label(droite, text="EquipementEnergie generee", style="Form.TLabel").pack(anchor="w", pady=(0, 4))

        saisie_taux = ttk.Frame(droite, style="Panel.TFrame")
        saisie_taux.pack(fill="x", pady=(0, 6))
        ttk.Label(saisie_taux, text="Taux pratique (%)", style="Form.TLabel").pack(side="left")
        self.taux_pratique_entry = ttk.Entry(saisie_taux, width=12)
        self.taux_pratique_entry.pack(side="left", padx=(8, 0))
        self.taux_pratique_entry.insert(0, "100")

        saisie_ps = ttk.Frame(droite, style="Panel.TFrame")
        saisie_ps.pack(fill="x", pady=(0, 8))
        ttk.Label(saisie_ps, text="Nombre PS", style="Form.TLabel").pack(side="left")
        self.nombre_ps_entry = ttk.Entry(saisie_ps, width=8)
        self.nombre_ps_entry.pack(side="left", padx=(8, 12))
        self.nombre_ps_entry.insert(0, "1")
        ttk.Label(saisie_ps, text="Energie unitaire", style="Form.TLabel").pack(side="left")
        self.energie_unitaire_entry = ttk.Entry(saisie_ps, width=12)
        self.energie_unitaire_entry.pack(side="left", padx=(8, 12))
        ttk.Label(saisie_ps, text="PU", style="Form.TLabel").pack(side="left")
        self.prix_unitaire_entry = ttk.Entry(saisie_ps, width=12)
        self.prix_unitaire_entry.pack(side="left", padx=(8, 0))

        colonnes_ee = ("equipement", "type", "taux", "nombre", "energie_unitaire", "prix_unitaire", "grandeur")
        self.table_ee = ttk.Treeview(droite, columns=colonnes_ee, show="headings", height=6)
        self.table_ee.heading("equipement", text="Equipement")
        self.table_ee.heading("type", text="Type")
        self.table_ee.heading("taux", text="Taux pratique (%)")
        self.table_ee.heading("nombre", text="Nombre")
        self.table_ee.heading("energie_unitaire", text="Energie unitaire")
        self.table_ee.heading("prix_unitaire", text="PU")
        self.table_ee.heading("grandeur", text="Grandeur energetique")
        self.table_ee.column("equipement", width=180)
        self.table_ee.column("type", width=80, anchor="center")
        self.table_ee.column("taux", width=120, anchor="center")
        self.table_ee.column("nombre", width=80, anchor="center")
        self.table_ee.column("energie_unitaire", width=120, anchor="e")
        self.table_ee.column("prix_unitaire", width=120, anchor="e")
        self.table_ee.column("grandeur", width=120, anchor="center")
        self.table_ee.pack(fill="x", expand=True)

        actions_eq = ttk.Frame(wrapper, style="Panel.TFrame")
        actions_eq.pack(fill="x", pady=(8, 6))
        ttk.Button(
            actions_eq,
            text="Creer la liste EquipementEnergie",
            style="Primary.TButton",
            command=self.appliquer_equipements_selectionnes,
        ).pack(side="left")

        bas = ttk.Frame(wrapper, style="Panel.TFrame")
        bas.pack(fill="x", pady=(8, 0))
        self.info_label = ttk.Label(bas, text="", style="Hint.TLabel")
        self.info_label.pack(side="left")
        ttk.Button(bas, text="Submit", style="Primary.TButton", command=self.submit_placeholder).pack(side="right")

    def _charger_donnees_utilisation(self) -> None:
        for ligne in self.table.get_children():
            self.table.delete(ligne)

        for detail in self.utilisations_locales:
            self.table.insert(
                "",
                "end",
                values=(
                    detail.materiel_puissance.materiel.libelle,
                    detail.tranche.libelle,
                    detail.heure_debut.strftime("%H:%M"),
                    detail.heure_fin.strftime("%H:%M"),
                    f"{detail.materiel_puissance.puissance:.2f}",
                ),
            )

        self.info_label.configure(
            text=(
                f"{len(self.utilisations_locales)} utilisation(s) chargee(s) depuis la base et "
                f"{len(self.equipements_energie_locaux)} equipement(s) energie selectionne(s)."
            )
        )

    def appliquer_equipements_selectionnes(self) -> None:
        indices = self.equipements_listbox.curselection()
        if not indices:
            messagebox.showwarning("Selection requise", "Selectionnez au moins un equipement.")
            return

        try:
            taux_pratique = float(self.taux_pratique_entry.get().strip())
        except ValueError:
            messagebox.showerror("Taux invalide", "Saisissez un taux pratique numerique.")
            return
        if taux_pratique <= 0:
            messagebox.showerror("Taux invalide", "Le taux pratique doit etre strictement positif.")
            return

        selections_a_enregistrer: list[dict[str, float | int]] = []
        for i in indices:
            equipement = self.equipements[i]
            type_equipement = equipement.type.strip().lower()
            enregistrement: dict[str, float | int] = {
                "equipement_id": equipement.id,
                "taux": taux_pratique,
                "nombre": 1,
            }

            if type_equipement == "ps":
                try:
                    nombre = int(self.nombre_ps_entry.get().strip())
                    energie_unitaire = float(self.energie_unitaire_entry.get().strip())
                    prix_unitaire = float(self.prix_unitaire_entry.get().strip())
                except ValueError:
                    messagebox.showerror(
                        "Valeurs PS invalides",
                        "Pour les equipements ps, saisissez un nombre entier, une energie unitaire et un prix unitaire valides.",
                    )
                    return
                if nombre <= 0 or energie_unitaire <= 0 or prix_unitaire <= 0:
                    messagebox.showerror(
                        "Valeurs PS invalides",
                        "Le nombre, l'energie unitaire et le prix unitaire doivent etre strictement positifs.",
                    )
                    return

                enregistrement["nombre"] = nombre
                enregistrement["energie_unitaire"] = energie_unitaire
                enregistrement["prix_unitaire"] = prix_unitaire

            self._taux_pratiques_par_equipement[equipement.id] = taux_pratique
            selections_a_enregistrer.append(enregistrement)

        try:
            equipements_crees, _ = self.controller.enregistrer_equipements_selectionnes(selections_a_enregistrer)
        except ValueError as erreur:
            messagebox.showerror("Synchronisation impossible", str(erreur))
            return

        self._selection_equipements.extend(selections_a_enregistrer)
        self.equipements_energie_locaux.extend(equipements_crees)

        for ligne in self.table_ee.get_children():
            self.table_ee.delete(ligne)

        for ee in self.equipements_energie_locaux:
            self.table_ee.insert(
                "",
                "end",
                values=(
                    ee.equipement.libelle,
                    ee.equipement.type,
                    f"{self._taux_pratiques_par_equipement.get(ee.equipement.id, 0.0):.2f}",
                    1,
                    "" if ee.energie_unitaire is None else f"{ee.energie_unitaire:.2f}",
                    "" if ee.prix_unitaire is None else f"{ee.prix_unitaire:.2f}",
                    "vide" if ee.grandeur_energetique is None else f"{ee.grandeur_energetique:.2f}",
                ),
            )

        self.info_label.configure(
            text=(
                f"{len(self.utilisations_locales)} utilisation(s) chargee(s) depuis la base et "
                f"{len(self.equipements_energie_locaux)} equipement(s) energie selectionne(s)."
            )
        )

    def submit_placeholder(self) -> None:
        if not self.utilisations_locales:
            messagebox.showwarning("Donnees manquantes", "Aucun UtilisationDetail charge depuis la base.")
            return
        if not self.equipements_energie_locaux:
            messagebox.showwarning("Donnees manquantes", "Selectionnez au moins un equipement avant submit.")
            return

        try:
            besoins_theoriques, besoins_pratiques, propositions_surplus, meilleure_proposition = self.controller.proposerEnsemble(
                self.utilisations_locales,
                self.equipements_energie_locaux,
                [],
            )
        except ValueError as erreur:
            messagebox.showerror("Calcul impossible", str(erreur))
            return

        FenetreBesoinsTheoriques(self, besoins_theoriques, besoins_pratiques, propositions_surplus, meilleure_proposition)

    @staticmethod
    def _label_equipement(equipement: Equipement) -> str:
        return f"{equipement.libelle} [{equipement.type}]"

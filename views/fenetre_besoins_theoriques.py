import tkinter as tk
from tkinter import ttk

from models.equipement_energie import EquipementEnergie
from models.proposition_surplus import PropositionSurplus


class FenetreBesoinsTheoriques(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Tk,
        besoins_theoriques: list[EquipementEnergie],
        besoins_pratiques: list[EquipementEnergie],
        propositions_surplus: list[PropositionSurplus],
        meilleure_proposition: PropositionSurplus | None,
    ) -> None:
        super().__init__(parent)
        self.title("Scenarios 2A et 2B - Besoins energetiques")
        self.geometry("960x760")
        self.minsize(820, 620)
        self.configure(bg="#f4f6f8")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"), background="#ffffff", foreground="#1f2d3d")
        style.configure("Hint.TLabel", font=("Segoe UI", 10), background="#ffffff", foreground="#5e6c79")
        style.configure("Section.TLabel", font=("Segoe UI", 11, "bold"), background="#ffffff", foreground="#1f2d3d")

        card = ttk.Frame(self, style="Card.TFrame", padding=20)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.92, relheight=0.88)

        ttk.Label(card, text="Sources d'energie necessaires", style="Title.TLabel").pack(anchor="w", pady=(0, 4))
        ttk.Label(card, text="Resultats theoriques en haut et pratiques en bas", style="Hint.TLabel").pack(anchor="w", pady=(0, 14))

        ttk.Label(card, text="Besoins theoriques", style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        self._creer_table(card, besoins_theoriques, hauteur=8).pack(fill="both", expand=True)

        ttk.Separator(card, orient="horizontal").pack(fill="x", pady=14)

        ttk.Label(card, text="Besoins pratiques", style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        self._creer_table(card, besoins_pratiques, hauteur=8).pack(fill="both", expand=True)

        ttk.Separator(card, orient="horizontal").pack(fill="x", pady=14)
        ttk.Label(card, text="Proposition de panneaux", style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        self._creer_table_surplus(card, propositions_surplus, hauteur=6).pack(fill="both", expand=True)

        proposition_txt = "Aucun panneau de type ps avec energie unitaire et prix unitaire n'a ete trouve."
        if meilleure_proposition is not None:
            proposition_txt = (
                f"Panneau recommande: {meilleure_proposition.equipement_energie.equipement.libelle} | "
                f"qte minimale: {meilleure_proposition.quantite_necessaire} | "
                f"cout total: {meilleure_proposition.prix_total:.2f}"
            )
        ttk.Label(card, text=proposition_txt, style="Hint.TLabel", wraplength=780, justify="left").pack(anchor="w", pady=(10, 0))

    def _creer_table(
        self,
        parent: ttk.Frame,
        besoins: list[EquipementEnergie],
        hauteur: int,
    ) -> ttk.Treeview:
        colonnes = ("equipement", "type_equipement", "type_resultat", "grandeur")
        table = ttk.Treeview(parent, columns=colonnes, show="headings", height=hauteur)
        table.heading("equipement", text="Equipement")
        table.heading("type_equipement", text="Type equipement")
        table.heading("type_resultat", text="Type resultat")
        table.heading("grandeur", text="Grandeur energetique")

        table.column("equipement", width=280)
        table.column("type_equipement", width=120, anchor="center")
        table.column("type_resultat", width=120, anchor="center")
        table.column("grandeur", width=180, anchor="e")

        for ee in besoins:
            grandeur = ee.grandeur_energetique if ee.grandeur_energetique is not None else 0.0
            table.insert(
                "",
                "end",
                values=(
                    ee.equipement.libelle,
                    ee.equipement.type,
                    ee.type_resultat,
                    f"{grandeur:.2f}",
                ),
            )

        return table

    def _creer_table_surplus(
        self,
        parent: ttk.Frame,
        propositions: list[PropositionSurplus],
        hauteur: int,
    ) -> ttk.Treeview:
        colonnes = ("equipement", "energie_unitaire", "prix_unitaire", "quantite", "prix_total")
        table = ttk.Treeview(parent, columns=colonnes, show="headings", height=hauteur)
        table.heading("equipement", text="Panneau")
        table.heading("energie_unitaire", text="Energie unitaire")
        table.heading("prix_unitaire", text="Prix unitaire")
        table.heading("quantite", text="Qte minimale")
        table.heading("prix_total", text="Prix total")

        table.column("equipement", width=260)
        table.column("energie_unitaire", width=140, anchor="e")
        table.column("prix_unitaire", width=140, anchor="e")
        table.column("quantite", width=110, anchor="center")
        table.column("prix_total", width=150, anchor="e")

        for proposition in propositions:
            ee = proposition.equipement_energie
            table.insert(
                "",
                "end",
                values=(
                    ee.equipement.libelle,
                    f"{(ee.energie_unitaire or 0.0):.2f}",
                    f"{(ee.prix_unitaire or 0.0):.2f}",
                    proposition.quantite_necessaire,
                    f"{proposition.prix_total:.2f}",
                ),
            )

        return table

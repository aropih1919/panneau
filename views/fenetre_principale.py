import tkinter as tk
from tkinter import ttk

from controllers.mon_controller import MonController
from views.fenetre_formulaire import FenetreFormulaire


class FenetrePrincipale(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Consommation avec panneau solaire")
        self.geometry("840x520")
        self.minsize(760, 480)
        self.configure(bg="#f4f6f8")

        self.controller = MonController()
        self._initialiser_style()
        self._construire_vue()

    def _initialiser_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("Titre.TLabel", font=("Segoe UI", 18, "bold"), background="#ffffff", foreground="#1f2d3d")
        style.configure("SousTitre.TLabel", font=("Segoe UI", 11), background="#ffffff", foreground="#4e5d6c")
        style.configure("Etat.TLabel", font=("Segoe UI", 10), background="#ffffff", foreground="#1f2d3d")
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=8)

    def _construire_vue(self) -> None:
        container = ttk.Frame(self, style="Card.TFrame", padding=28)
        container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.82, relheight=0.72)

        ttk.Label(
            container,
            text="Scenario 1 - Entree des besoins de materiel",
            style="Titre.TLabel",
        ).pack(anchor="w", pady=(0, 8))

        ttk.Label(
            container,
            text=(
                "Formulaire de saisie multiple avec references Materiel/Tranche/Equipement "
                "chargees depuis la base."
            ),
            style="SousTitre.TLabel",
            wraplength=620,
            justify="left",
        ).pack(anchor="w", pady=(0, 18))

        ttk.Label(container, text=self.controller.verifier_systeme(), style="Etat.TLabel").pack(anchor="w", pady=(0, 24))

        ttk.Button(
            container,
            text="Ouvrir le formulaire scenario 1",
            style="Action.TButton",
            command=self.ouvrir_formulaire,
        ).pack(anchor="w")

    def ouvrir_formulaire(self) -> None:
        FenetreFormulaire(self, self.controller)

import tkinter as tk

from views.fenetre_principale import FenetrePrincipale


def main() -> None:
    try:
        app = FenetrePrincipale()
        app.mainloop()
    except tk.TclError as erreur:
        print("Impossible d'ouvrir la fenetre graphique dans cet environnement.")
        print(f"Detail: {erreur}")


if __name__ == "__main__":
    main()

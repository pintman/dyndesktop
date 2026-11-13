"""Kartentyp-Basisklasse (D2)."""
from pathlib import Path


class BearbeitungsFehler(Exception):
    """Übernehmen abgelehnt. Die Meldung erscheint als Hinweis in der Bearbeitung."""


class Kartentyp:
    """Basis für alle Kartentypen.

    Ein Typ erzeugt den Inhalt einer Karte (ein Kivy-Widget) und legt fest,
    wie die Bearbeitung wirkt. Gesten, Schwung und Langdruck liefert die Karte.
    """

    name: str = ""
    endungen: tuple[str, ...] = ()
    mehrzeilig = False          # Eingabefeld der Bearbeitung mehrzeilig?

    def erzeuge_inhalt(self, pfad: Path):
        """Widget für die Datei. Darf werfen → Fehlerkarte."""
        raise NotImplementedError

    def groesse(self, inhalt) -> tuple[float, float]:
        """Kartengröße (Seitenverhältnis des Inhalts)."""
        return 400, 300

    def raeume_auf(self, inhalt) -> None:
        """Inhalt wird von der Karte entfernt (z. B. Video stoppen)."""

    def bearbeitungswert(self, pfad: Path, inhalt) -> str:
        """Startwert des Eingabefelds."""
        return Path(pfad).name

    def uebernehme(self, karte, wert: str) -> None:
        """Wert übernehmen. Wirft BearbeitungsFehler mit Hinweistext."""
        raise BearbeitungsFehler("Dieser Kartentyp ist nicht bearbeitbar.")

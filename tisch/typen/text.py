"""Textkarte: .txt als UTF-8, umbrochen an der Kartenbreite."""
from pathlib import Path

from kivy.metrics import dp
from kivy.uix.label import Label

from ..inhalte import schreibe_text
from ..karte import hintergrund
from .basis import BearbeitungsFehler, Kartentyp


class TextTyp(Kartentyp):
    name = "text"
    endungen = (".txt",)
    mehrzeilig = True

    def erzeuge_inhalt(self, pfad):
        text = Path(pfad).read_text(encoding="utf-8")
        lbl = Label(text=text, color=(0.1, 0.1, 0.12, 1), font_size=dp(18),
                    halign="left", valign="top", padding=dp(16))
        lbl.bind(size=lambda w, s: setattr(w, "text_size", s))
        return hintergrund(lbl, (0.97, 0.95, 0.88, 1))

    def groesse(self, inhalt):
        return 400, 300

    def bearbeitungswert(self, pfad, inhalt):
        return inhalt.text

    def uebernehme(self, karte, wert):
        try:
            schreibe_text(karte.pfad, wert)
        except OSError as e:
            raise BearbeitungsFehler(f"Speichern fehlgeschlagen: {e.strerror or e}") from e
        karte.inhalt.text = wert

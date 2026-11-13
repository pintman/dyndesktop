"""Bildkarte: Seitenverhältnis des Bildes, ohne Verzerrung."""
from pathlib import Path

from kivy.uix.image import Image

from ..inhalte import DateinameFehler, pruefe_dateiname
from ..karte import kartengroesse
from .basis import BearbeitungsFehler, Kartentyp


def wechsle_datei(karte, name, typ):
    """Karte auf eine andere Datei im Inhaltsordner umstellen (Bild und Video)."""
    try:
        pfad = pruefe_dateiname(karte.pfad.parent, name, typ)
    except DateinameFehler as e:
        raise BearbeitungsFehler(str(e)) from e
    if pfad == karte.pfad:
        return
    try:
        inhalt = typ.erzeuge_inhalt(pfad)
        groesse = typ.groesse(inhalt)
    except Exception as e:  # noqa: BLE001
        raise BearbeitungsFehler(f"{pfad.name} lässt sich nicht öffnen: {e}") from e
    karte.pfad = pfad
    karte.passe_groesse(*groesse)
    karte.setze_inhalt(inhalt)


class BildTyp(Kartentyp):
    name = "bild"
    endungen = (".jpg", ".jpeg", ".png")

    def erzeuge_inhalt(self, pfad):
        if not Path(pfad).is_file():
            raise FileNotFoundError(f"{Path(pfad).name} fehlt")
        img = Image(source=str(pfad), fit_mode="contain")
        if img.texture is None:
            raise ValueError("Bild lässt sich nicht lesen")
        return img

    def groesse(self, inhalt):
        return kartengroesse(*inhalt.texture_size)

    def uebernehme(self, karte, wert):
        wechsle_datei(karte, wert, self)

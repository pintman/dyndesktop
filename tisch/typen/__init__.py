"""Registry der Kartentypen.

Neuen Typ anmelden:  registriere(MeinTyp())
Die eingebauten Typen (Text, Bild, Video) melden sich beim Import an.
"""
from pathlib import Path

from .basis import BearbeitungsFehler, Kartentyp


class Registry:
    def __init__(self):
        self._typen: dict[str, Kartentyp] = {}

    def registriere(self, typ: Kartentyp) -> Kartentyp:
        neu = [e.lower() for e in typ.endungen]
        for e in neu:
            if e in self._typen:
                raise ValueError(
                    f"Endung {e} gehört bereits zum Kartentyp '{self._typen[e].name}'")
        for e in neu:
            self._typen[e] = typ
        return typ

    def typ_fuer(self, pfad) -> Kartentyp | None:
        return self._typen.get(Path(pfad).suffix.lower())

    def endungen(self) -> set[str]:
        return set(self._typen)


_standard = Registry()
registriere = _standard.registriere
typ_fuer = _standard.typ_fuer
endungen = _standard.endungen

__all__ = ["BearbeitungsFehler", "Kartentyp", "Registry",
           "registriere", "typ_fuer", "endungen"]

# eingebaute Typen (Import erst hier, sie nutzen Kartentyp)
from .bild import BildTyp    # noqa: E402
from .text import TextTyp    # noqa: E402
from .video import VideoTyp  # noqa: E402

registriere(TextTyp())
registriere(BildTyp())
registriere(VideoTyp())

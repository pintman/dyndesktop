"""Videokarte: stumm, Endlosschleife, Seitenverhältnis des Videos (D8)."""
from pathlib import Path

from kivy.clock import Clock
from kivy.uix.video import Video

from ..karte import kartengroesse
from .basis import Kartentyp
from .bild import wechsle_datei

PRUEFZEIT = 3  # s ohne erstes Bild → Fehlerkarte


class VideoTyp(Kartentyp):
    name = "video"
    endungen = (".mp4", ".webm")

    def erzeuge_inhalt(self, pfad):
        if not Path(pfad).is_file():
            raise FileNotFoundError(f"{Path(pfad).name} fehlt")
        v = Video(source=str(pfad), state="play", volume=0,
                  options={"eos": "loop"}, fit_mode="contain")
        v.bind(texture=self._neue_textur)
        v._tisch_pruefung = Clock.schedule_once(lambda dt: self._pruefe(v), PRUEFZEIT)
        v._tisch_seiten = None
        return v

    def groesse(self, inhalt):
        if inhalt.texture:
            return kartengroesse(*inhalt.texture_size)
        return kartengroesse(16, 9)

    def _neue_textur(self, v, tex):
        karte = v.parent
        if tex is None or karte is None or karte.inhalt is not v:
            return
        seiten = tuple(tex.size)
        if seiten != v._tisch_seiten:
            v._tisch_seiten = seiten
            karte.passe_groesse(*kartengroesse(*seiten))

    def _pruefe(self, v):
        karte = v.parent
        if v.texture is None and karte is not None and karte.inhalt is v:
            karte.zeige_fehler("Video lässt sich nicht abspielen")

    def raeume_auf(self, inhalt):
        inhalt._tisch_pruefung.cancel()
        inhalt.state = "stop"
        inhalt.unload()

    def uebernehme(self, karte, wert):
        wechsle_datei(karte, wert, self)

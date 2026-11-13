"""TischApp: Fläche, Karten aus dem Inhaltsordner, Anordnung (D9, D10)."""
import math
import random
from pathlib import Path

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label

from . import typen
from .inhalte import scanne
from .karte import SchwungKarte

ZELLE_MIN = (200, 160)   # kleinere Rasterzellen → Karten liegen versetzt übereinander
VERSATZ = 30
DREHUNG = 8              # ± Grad
SEED = 7


def lade_karten(ordner, registry=None, bei_langdruck=None):
    """Je unterstützter Datei eine SchwungKarte (Fehlerkarte, wenn Laden scheitert)."""
    reg = registry or typen._standard
    return [SchwungKarte(reg.typ_fuer(p), p, bei_langdruck=bei_langdruck)
            for p in scanne(ordner, reg.endungen())]


def anordnen(karten, breite, hoehe):
    """Raster nach Reihenfolge, leichte Zufallsdrehung, alles im Fenster."""
    n = len(karten)
    if not n:
        return
    max_sp = max(1, int(breite // ZELLE_MIN[0]))
    max_ze = max(1, int(hoehe // ZELLE_MIN[1]))
    platz = max_sp * max_ze
    m = min(n, platz)
    sp = min(max_sp, max(1, math.ceil(math.sqrt(m * breite / hoehe))))
    ze = min(max_ze, math.ceil(m / sp))
    sp = math.ceil(m / ze)
    zw, zh = breite / sp, hoehe / ze
    rnd = random.Random(SEED)
    for i, k in enumerate(karten):
        zelle, lage = i % platz, i // platz
        cx = (zelle % sp + 0.5) * zw + lage * VERSATZ
        cy = hoehe - (zelle // sp + 0.5) * zh - lage * VERSATZ
        k.scale = max(k.scale_min, min(1.0, 0.85 * zw / k.width, 0.85 * zh / k.height))
        k.rotation = rnd.uniform(-DREHUNG, DREHUNG)
        k.center = (min(max(cx, 0), breite), min(max(cy, 0), hoehe))


class TischApp(App):
    title = "Tisch"

    def __init__(self, inhalte, **kw):
        super().__init__(**kw)
        self.inhalte = Path(inhalte)

    def build(self):
        # spät: Window/TextInput öffnen ein Fenster, lade_karten bleibt fensterlos testbar
        from kivy.core.window import Window

        from . import bearbeitung

        Window.clearcolor = (0.12, 0.12, 0.14, 1)
        root = FloatLayout()
        karten = lade_karten(self.inhalte, bei_langdruck=bearbeitung.oeffne)
        if not karten:
            root.add_widget(Label(text=f"Keine Inhalte in {self.inhalte}",
                                  font_size="22sp", color=(0.8, 0.8, 0.8, 1)))
        anordnen(karten, *Window.size)
        for k in karten:
            root.add_widget(k)
        return root

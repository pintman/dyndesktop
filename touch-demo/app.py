"""Touch-Tisch mit Kivy.

Jede Karte ist ein Scatter: verschieben, drehen, skalieren per Multitouch.
Bilder aus ./bilder werden geladen, sonst farbige Platzhalter.

Setup:  poetry install
Start:  poetry run python touch-demo/app.py
Am Mac: Rechtsklick setzt einen zweiten "Finger" (roter Punkt) zum Drehen/Zoomen.
"""
from pathlib import Path

from kivy.app import App
from kivy.core.window import Window
from kivy.effects.kinetic import KineticEffect
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.scatter import Scatter

BILDER = Path(__file__).parent / "bilder"
FARBEN = [(0.9, 0.3, 0.3), (0.3, 0.7, 0.4), (0.3, 0.5, 0.9), (0.9, 0.7, 0.2)]


class SchwungKarte(Scatter):
    """Scatter mit Trägheit: rutscht nach dem Loslassen weiter (nur bei 1 Finger)."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self._multi = False
        self.kx = KineticEffect(friction=0.05)
        self.ky = KineticEffect(friction=0.05)
        self.kx.bind(value=lambda e, v: self._rutsche(e, 0, v))
        self.ky.bind(value=lambda e, v: self._rutsche(e, 1, v))

    def _rutsche(self, effekt, achse, v):
        if effekt.is_manual:          # während Drag bewegt Scatter selbst
            return
        grenze = Window.width if achse == 0 else Window.height
        if not 0 <= v <= grenze:      # am Fensterrand anhalten
            v = min(max(v, 0), grenze)
            effekt.velocity = 0
        c = list(self.center)
        c[achse] = v
        self.center = c

    def _alle(self, methode):
        for e, v in ((self.kx, self.center_x), (self.ky, self.center_y)):
            getattr(e, methode)(v)

    def on_touch_down(self, touch):
        r = super().on_touch_down(touch)
        if touch.grab_current is self or touch in self._touches:
            if len(self._touches) == 1:
                self._multi = False
                self._alle("start")   # setzt velocity=0 -> stoppt Ausrollen
                self.kx.value, self.ky.value = self.center
            else:
                self._multi = True
        return r

    def on_touch_move(self, touch):
        r = super().on_touch_move(touch)
        if touch.grab_current is self and self.kx.is_manual:
            self._alle("update")
        return r

    def on_touch_up(self, touch):
        letzter = touch in self._touches and len(self._touches) == 1
        r = super().on_touch_up(touch)
        if letzter and self.kx.is_manual:
            if self._multi:           # nach Drehen/Zoomen kein Schwung
                for e in (self.kx, self.ky):
                    e.is_manual = False
                    e.velocity = 0
            else:
                self.kx.value, self.ky.value = self.center
                self._alle("stop")
        return r


def kartengroesse(inhalt, max_seite=400):
    """Bilder behalten ihr Seitenverhältnis, längste Seite = max_seite."""
    if isinstance(inhalt, Image) and inhalt.texture:
        w, h = inhalt.texture_size
        f = max_seite / max(w, h)
        return w * f, h * f
    return 400, 300


def karte(inhalt, pos):
    s = SchwungKarte(size=kartengroesse(inhalt), pos=pos, do_rotation=True, do_scale=True,
                     scale_min=0.3, scale_max=4)
    inhalt.size = s.size
    s.add_widget(inhalt)
    return s


def platzhalter(text, farbe):
    lbl = Label(text=text, font_size=40)
    with lbl.canvas.before:
        Color(*farbe)
        rect = Rectangle(pos=lbl.pos, size=lbl.size)
    lbl.bind(pos=lambda w, v: setattr(rect, "pos", v),
             size=lambda w, v: setattr(rect, "size", v))
    return lbl


class Tisch(App):
    def build(self):
        Window.clearcolor = (0.12, 0.12, 0.14, 1)
        # Window.fullscreen = "auto"   # auf dem Tisch aktivieren
        root = FloatLayout()

        dateien = sorted(p for p in BILDER.glob("*")
                         if p.suffix.lower() in {".jpg", ".jpeg", ".png"}) if BILDER.exists() else []
        if dateien:
            inhalte = [Image(source=str(p), fit_mode="contain") for p in dateien]
        else:
            inhalte = [platzhalter(f"Karte {i + 1}", f) for i, f in enumerate(FARBEN)]

        for i, w in enumerate(inhalte):
            root.add_widget(karte(w, pos=(50 + (i % 3) * 450, 80 + (i // 3) * 350)))
        return root


if __name__ == "__main__":
    Tisch().run()

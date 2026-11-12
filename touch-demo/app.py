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
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.scatter import Scatter

BILDER = Path(__file__).parent / "bilder"
FARBEN = [(0.9, 0.3, 0.3), (0.3, 0.7, 0.4), (0.3, 0.5, 0.9), (0.9, 0.7, 0.2)]


def karte(inhalt, pos):
    s = Scatter(size=(400, 300), pos=pos, do_rotation=True, do_scale=True,
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

"""SchwungKarte: Scatter mit Trägheit und Langdruck (aus touch-demo/app.py)."""
import time
from pathlib import Path

from kivy.clock import Clock
from kivy.effects.kinetic import KineticEffect
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.uix.scatter import Scatter

from . import langdruck

MAX_SEITE = 400


def kartengroesse(w, h, max_seite=MAX_SEITE):
    """Seitenverhältnis w:h, längste Seite = max_seite."""
    if not w or not h:
        return max_seite, max_seite * 3 / 4
    f = max_seite / max(w, h)
    return w * f, h * f


def hintergrund(widget, farbe):
    """Farbige Fläche hinter einem Widget, folgt pos/size."""
    with widget.canvas.before:
        Color(*farbe)
        rect = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda w, v: setattr(rect, "pos", v),
                size=lambda w, v: setattr(rect, "size", v))
    return widget


def fehleranzeige(name, meldung):
    lbl = Label(text=f"[b]{name}[/b]\n\n{meldung}", markup=True, halign="center",
                valign="middle", color=(1, 1, 1, 1), padding=dp(12))
    lbl.bind(size=lambda w, s: setattr(w, "text_size", s))
    return hintergrund(lbl, (0.4, 0.4, 0.42, 1))


class SchwungKarte(Scatter):
    """Karte eines Kartentyps. Rutscht nach dem Loslassen weiter (nur bei 1 Finger).

    `bei_langdruck(karte)` wird nach einem langen Touch aufgerufen.
    """

    def __init__(self, typ, pfad, bei_langdruck=None, **kw):
        for k, v in dict(do_rotation=True, do_scale=True, size_hint=(None, None),
                         scale_min=0.3, scale_max=4).items():
            kw.setdefault(k, v)
        super().__init__(**kw)
        self.typ = typ
        self.pfad = Path(pfad)
        self.bei_langdruck = bei_langdruck
        self.fehler = None
        self.inhalt = None
        try:
            inhalt = typ.erzeuge_inhalt(self.pfad)
            self.size = typ.groesse(inhalt)
        except Exception as e:  # noqa: BLE001 – jede Ladeursache → Fehlerkarte
            self.fehler = str(e) or type(e).__name__
            inhalt = fehleranzeige(self.pfad.name, self.fehler)
            self.size = kartengroesse(4, 3)
        self.setze_inhalt(inhalt)
        self.bind(size=self._kinder_anpassen)

        self._multi = False
        self.kx = KineticEffect(friction=0.05)
        self.ky = KineticEffect(friction=0.05)
        self.kx.bind(value=lambda e, v: self._rutsche(e, 0, v))
        self.ky.bind(value=lambda e, v: self._rutsche(e, 1, v))

        self._lang = langdruck.Erkenner(schwelle=dp(langdruck.SCHWELLE))
        self._lang_touch = None
        self._lang_ev = None

    # --- Inhalt -------------------------------------------------------------

    def setze_inhalt(self, widget):
        """Inhalt tauschen. Er liegt unter allen anderen Kindern (Overlay, Hinweis)."""
        if self.inhalt is not None:
            self.remove_widget(self.inhalt)
            self.typ.raeume_auf(self.inhalt)
        self.inhalt = widget
        widget.pos = (0, 0)
        widget.size_hint = (None, None)
        widget.size = self.size
        self.add_widget(widget, index=len(self.children))

    def zeige_fehler(self, meldung):
        self.fehler = meldung
        self.setze_inhalt(fehleranzeige(self.pfad.name, meldung))

    def passe_groesse(self, w, h):
        """Neue Größe, Mittelpunkt, Drehung und Skalierung bleiben."""
        c = self.center
        self.size = (w, h)
        self.center = c

    def _kinder_anpassen(self, _, size):
        for k in self.children:
            if k is self.inhalt or getattr(k, "fuellt_karte", False):
                k.size = size

    # --- Schwung ------------------------------------------------------------

    def _rutsche(self, effekt, achse, v):
        if effekt.is_manual:          # während Drag bewegt Scatter selbst
            return
        flaeche = self.parent.size if self.parent else (v, v)
        grenze = flaeche[achse]
        if not 0 <= v <= grenze:      # am Rand anhalten
            v = min(max(v, 0), grenze)
            effekt.velocity = 0
        c = list(self.center)
        c[achse] = v
        self.center = c

    def _alle(self, methode):
        for e, v in ((self.kx, self.center_x), (self.ky, self.center_y)):
            getattr(e, methode)(v)

    def _schwung_aus(self):
        for e in (self.kx, self.ky):
            e.is_manual = False
            e.velocity = 0

    # --- Touch --------------------------------------------------------------

    def on_touch_down(self, touch):
        r = super().on_touch_down(touch)
        if touch.grab_current is self or touch in self._touches:
            if len(self._touches) == 1:
                self._multi = False
                self._alle("start")   # setzt velocity=0 -> stoppt Ausrollen
                self.kx.value, self.ky.value = self.center
            else:
                self._multi = True
            self._lang.down(touch.uid, touch.pos, time.monotonic())
            if self._lang.wartet:
                self._lang_touch = touch
                self._plane_pruefung(self._lang.dauer)
        return r

    def on_touch_move(self, touch):
        r = super().on_touch_move(touch)
        if touch.grab_current is self:
            self._lang.move(touch.uid, touch.pos)
            if self.kx.is_manual:
                self._alle("update")
        return r

    def on_touch_up(self, touch):
        letzter = touch in self._touches and len(self._touches) == 1
        r = super().on_touch_up(touch)
        self._lang.up(touch.uid)
        if letzter and self.kx.is_manual:
            if self._multi:           # nach Drehen/Zoomen kein Schwung
                self._schwung_aus()
            else:
                self.kx.value, self.ky.value = self.center
                self._alle("stop")
        return r

    # --- Langdruck ----------------------------------------------------------

    def _plane_pruefung(self, nach):
        if self._lang_ev is not None:
            self._lang_ev.cancel()
        self._lang_ev = Clock.schedule_once(self._pruefe_langdruck, nach)

    def _pruefe_langdruck(self, _dt):
        self._lang_ev = None
        if self._lang.faellig(time.monotonic()):
            self._langdruck()
        elif self._lang.wartet:       # Clock war minimal zu früh
            self._plane_pruefung(0.05)

    def _langdruck(self):
        touch, self._lang_touch = self._lang_touch, None
        self._schwung_aus()
        if touch is not None and touch in self._touches:
            touch.ungrab(self)
            self._touches.remove(touch)
            self._last_touch_pos.pop(touch, None)
        if self.bei_langdruck:
            self.bei_langdruck(self)

"""Bearbeitung einer Karte: Overlay in der Karte + virtuelle Tastatur (D6, D7)."""
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.vector import Vector

from .karte import hintergrund
from .tastatur import TischTastatur
from .typen import BearbeitungsFehler

HINWEIS_DAUER = 1.5   # s
ABSTAND = 10          # dp zwischen Karte und Tastatur

aktive = None          # die eine offene Bearbeitung


class Bearbeitung(FloatLayout):
    fuellt_karte = True   # SchwungKarte passt die Größe an

    def __init__(self, karte, **kw):
        super().__init__(size_hint=(None, None), size=karte.size, pos=(0, 0), **kw)
        self.karte = karte
        typ = karte.typ
        hintergrund(self, (0.1, 0.1, 0.12, 0.85))

        mehr = typ.mehrzeilig
        self.feld = TextInput(
            text=typ.bearbeitungswert(karte.pfad, karte.inhalt),
            multiline=mehr, unfocus_on_touch=False, text_validate_unfocus=False,
            font_size=dp(16), write_tab=False,
            size_hint=(0.94, 0.62 if mehr else 0.2),
            pos_hint={"center_x": 0.5, "top": 0.97})
        if not mehr:
            self.feld.bind(on_text_validate=lambda *_: self.uebernehmen())
        self.feld.bind(focus=self._fokus)
        self.add_widget(self.feld)

        self.fehlerzeile = Label(text="", color=(1, 0.35, 0.3, 1), font_size=dp(14),
                                 halign="center", valign="middle",
                                 size_hint=(0.94, 0.14),
                                 pos_hint={"center_x": 0.5, "y": 0.2})
        self.fehlerzeile.bind(size=lambda w, s: setattr(w, "text_size", s))
        self.add_widget(self.fehlerzeile)

        knoepfe = BoxLayout(spacing=dp(8), size_hint=(0.94, 0.15),
                            pos_hint={"center_x": 0.5, "y": 0.03})
        knoepfe.add_widget(Button(text="Übernehmen", on_release=lambda *_: self.uebernehmen()))
        knoepfe.add_widget(Button(text="Abbrechen", on_release=lambda *_: schliesse()))
        self.add_widget(knoepfe)

    def _fokus(self, _, fokus):
        # Fokus weg, ohne dass wir schließen (✕-Taste der Tastatur) → Abbrechen
        if not fokus and aktive is self:
            schliesse()

    def uebernehmen(self):
        try:
            self.karte.typ.uebernehme(self.karte, self.feld.text)
        except BearbeitungsFehler as e:
            self.fehlerzeile.text = str(e)
            return
        schliesse()


def oeffne(karte):
    """Bearbeitung öffnen (Rückruf des Langdrucks)."""
    global aktive
    if aktive is not None:
        if aktive.karte is not karte:
            hinweis(karte, "Es ist bereits eine Bearbeitung offen.")
        return
    if karte.fehler:
        hinweis(karte, "Diese Karte lässt sich nicht bearbeiten.")
        return
    aktive = Bearbeitung(karte)
    karte.add_widget(aktive)
    aktive.feld.focus = True
    platziere_tastatur(aktive.feld, karte)


def schliesse():
    """Bearbeitung ohne weitere Änderung schließen, Tastatur verschwindet."""
    global aktive
    if aktive is None:
        return
    b, aktive = aktive, None
    b.feld.focus = False          # release_keyboard entfernt die Tastatur
    if b.parent:
        b.parent.remove_widget(b)


def tastatur_von(feld):
    kb = getattr(feld, "_keyboard", None)
    w = getattr(kb, "widget", None)
    if isinstance(w, TischTastatur):
        return w
    win = feld.get_parent_window()
    for kind in (win.children if win else []):
        if isinstance(kind, TischTastatur) and getattr(kind, "target", None) is feld:
            return kind
    return None


def _lege_an(kb, kb_punkt, ziel):
    """Verschiebt kb so, dass kb_punkt (lokal) auf ziel (Fenster) liegt."""
    ist = Vector(kb.to_parent(*kb_punkt))
    kb.pos = Vector(kb.pos) + (Vector(ziel) - ist)


def _schiebe_rein(kb, win):
    """Bounding Box so weit verschieben, dass sie im Fenster liegt (soweit möglich)."""
    (x, y), (w, h) = kb.bbox
    dx = max(0, -x) or min(0, win.width - (x + w))
    dy = max(0, -y) or min(0, win.height - (y + h))
    kb.pos = (kb.x + dx, kb.y + dy)


def _ueberdeckung(a, b):
    """Fläche, in der sich die Bounding Boxes von a und b überdecken."""
    (ax, ay), (aw, ah) = a.bbox
    (bx, by), (bw, bh) = b.bbox
    w = min(ax + aw, bx + bw) - max(ax, bx)
    h = min(ay + ah, by + bh) - max(ay, by)
    return max(0, w) * max(0, h)


def platziere_tastatur(feld, karte):
    """Tastatur in Drehung der Karte neben die Karte legen.

    Aus Kartensicht unter oder über die Karte, jeweils ins Fenster geschoben.
    Gewählt wird die Lage, die die Karte am wenigsten verdeckt (bei Gleichstand unten).
    """
    kb = tastatur_von(feld)
    if kb is None:
        return
    win = kb.get_parent_window()
    kb.rotation = karte.rotation
    if win:
        kb.scale = max(kb.scale_min, min(1.0, 0.95 * win.width / kb.width,
                                         0.45 * win.height / kb.height))
    abstand = dp(ABSTAND)
    lagen = [((kb.width / 2, kb.height),
              karte.to_window(karte.width / 2, -abstand, initial=False)),
             ((kb.width / 2, 0),
              karte.to_window(karte.width / 2, karte.height + abstand, initial=False))]
    bewertet = []
    for kb_punkt, ziel in lagen:
        _lege_an(kb, kb_punkt, ziel)
        if win:
            _schiebe_rein(kb, win)
        bewertet.append((_ueberdeckung(kb, karte), tuple(kb.pos)))
    kb.pos = min(bewertet, key=lambda b: b[0])[1]


def hinweis(karte, text):
    lbl = Label(text=text, font_size=dp(15), color=(1, 1, 1, 1),
                size_hint=(None, None), size=(karte.width, dp(40)),
                pos=(0, karte.height / 2 - dp(20)))
    hintergrund(lbl, (0.75, 0.2, 0.15, 0.9))
    karte.add_widget(lbl)
    Clock.schedule_once(lambda dt: lbl.parent and lbl.parent.remove_widget(lbl),
                        HINWEIS_DAUER)

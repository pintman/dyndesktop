"""Virtuelle Tastatur: deutsche Belegung, frei beweglich (D6)."""
from kivy.uix.vkeyboard import VKeyboard

STARTGROESSE = (700, 260)   # px, nach Abnahme am 40"-Tisch anpassen


class TischTastatur(VKeyboard):
    """Verschieben, Drehen, Skalieren über den Rand (breiter oberer Griff).

    Berührungen auf Tasten lösen Tasten aus, Berührungen im Rand bewegen die
    Tastatur. Als Scatter ohne KineticEffect rutscht sie nicht nach.
    """

    def __init__(self, **kw):
        kw.setdefault("layout", "qwertz")
        kw.setdefault("size", STARTGROESSE)
        kw.setdefault("margin_hint", [.12, .03, .03, .03])
        kw.setdefault("scale_min", .4)
        kw.setdefault("scale_max", 3)
        kw.setdefault("docked", False)
        super().__init__(**kw)

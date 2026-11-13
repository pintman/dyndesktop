"""Erkennung des langen Touchs (D5). Reine Logik ohne Kivy.

Schwellen nach dem Touchtest am Gerät anpassen.
"""
import math

DAUER = 0.8       # Sekunden
SCHWELLE = 10     # dp, die Karte rechnet in px um


class Erkenner:
    """Ein Finger, `dauer` lang höchstens `schwelle` bewegt → fällig.

    Ein zweiter aktiver Finger, Bewegung über der Schwelle oder Loslassen
    brechen ab. `faellig` meldet True genau einmal und gibt den Finger frei.
    """

    def __init__(self, dauer=DAUER, schwelle=SCHWELLE):
        self.dauer = dauer
        self.schwelle = schwelle
        self._aktive: set = set()
        self._uid = None
        self._start = (0.0, 0.0)
        self._t0 = 0.0

    @property
    def wartet(self) -> bool:
        return self._uid is not None

    def down(self, uid, pos, t):
        self._aktive.add(uid)
        if len(self._aktive) == 1:
            self._uid, self._start, self._t0 = uid, tuple(pos), t
        else:
            self._uid = None

    def move(self, uid, pos):
        if uid == self._uid and math.dist(pos, self._start) > self.schwelle:
            self._uid = None

    def up(self, uid):
        self._aktive.discard(uid)
        if uid == self._uid:
            self._uid = None

    def faellig(self, t) -> bool:
        if self._uid is not None and t - self._t0 >= self.dauer:
            self._aktive.discard(self._uid)
            self._uid = None
            return True
        return False

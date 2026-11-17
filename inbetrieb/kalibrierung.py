"""Kalibrier-Mathematik (D6): Rohpunkte → rotation/invert + ratio/offset.

Koordinaten sind normiert (0..1, Ursprung unten links wie in Kivy). „Roh“ heißt:
erfasst mit rotation=0, invert_x=0, invert_y=0 und ohne postproc (Rohmodus, D5).
Dann ist ein Rohpunkt genau (vx, vy) aus Kivys Kette, vor invert und rotation.
"""
import math
from dataclasses import asdict, dataclass

ROTATIONEN = (0, 90, 180, 270)
SCHWELLE = 0.02        # Anteil der Fensterdiagonale


def _zuweisen(punkt, wert, invert, achsen, rotation):
    """Nachbau von assign_coord aus kivy/input/providers/hidinput.py (und mtdev.py)."""
    cx, cy = achsen
    if invert:
        wert = 1.0 - wert
    if rotation == 0:
        punkt[cx] = wert
    elif rotation == 90:
        punkt[cy] = wert
    elif rotation == 180:
        punkt[cx] = 1.0 - wert
    elif rotation == 270:
        punkt[cy] = 1.0 - wert


def kette(vx, vy, rotation=0, invert_x=0, invert_y=0,
          xratio=1.0, yratio=1.0, xoffset=0.0, yoffset=0.0):
    """Kivys Transformation: (vx, vy) → invert → rotation → postproc:calibration.

    vx = normalize(ABS_X), vy = 1 - normalize(ABS_Y) – so berechnet es der Provider
    vor assign_coord.
    """
    p = {"x": 0.0, "y": 0.0}
    _zuweisen(p, vx, invert_x, ("x", "y"), rotation)
    _zuweisen(p, vy, invert_y, ("y", "x"), rotation)
    return p["x"] * xratio + xoffset, p["y"] * yratio + yoffset


@dataclass
class Kalibrierung:
    rotation: int = 0
    invert_x: int = 0
    invert_y: int = 0
    xratio: float = 1.0
    yratio: float = 1.0
    xoffset: float = 0.0
    yoffset: float = 0.0
    fehler: float = 0.0          # Quadratsumme der Residuen (normiert)

    def anwenden(self, vx, vy):
        return kette(vx, vy, self.rotation, self.invert_x, self.invert_y,
                     self.xratio, self.yratio, self.xoffset, self.yoffset)

    def werte(self):
        """Argumente für kivyconfig.setze_kalibrierung."""
        d = asdict(self)
        d.pop("fehler")
        return d


def regression(ist, soll):
    """soll ≈ ist * ratio + offset (kleinste Quadrate) → (ratio, offset, quadratsumme)."""
    n = len(ist)
    mi, ms = sum(ist) / n, sum(soll) / n
    var = sum((i - mi) ** 2 for i in ist)
    if var < 1e-12:
        return None
    ratio = sum((i - mi) * (s - ms) for i, s in zip(ist, soll)) / var
    offset = ms - ratio * mi
    rest = sum((i * ratio + offset - s) ** 2 for i, s in zip(ist, soll))
    return ratio, offset, rest


def bestimme(soll, roh):
    """Kalibrierung aus Paaren (soll normiert, roh normiert), mind. 3 Punkte.

    Probiert alle 16 Kombinationen (8 verschiedene Abbildungen). Nur positive
    ratio zählt, sonst stünde eine Spiegelung doppelt (invert vs. ratio < 0).
    Gleichwertige Kombinationen (r, ix, iy) ≡ (r+180, 1-ix, 1-iy) werden auf die
    Form mit den wenigsten Spiegelungen, dann kleinster Drehung reduziert.
    """
    if len(soll) != len(roh) or len(soll) < 3:
        raise ValueError("mindestens 3 Punktpaare nötig")
    beste = None
    for rot in ROTATIONEN:
        for ix in (0, 1):
            for iy in (0, 1):
                t = [kette(vx, vy, rot, ix, iy) for vx, vy in roh]
                rx = regression([p[0] for p in t], [s[0] for s in soll])
                ry = regression([p[1] for p in t], [s[1] for s in soll])
                if not rx or not ry or rx[0] <= 0 or ry[0] <= 0:
                    continue
                k = Kalibrierung(rot, ix, iy, rx[0], ry[0], rx[1], ry[1], rx[2] + ry[2])
                schluessel = (round(k.fehler, 9), ix + iy, rot)
                if beste is None or schluessel < beste[0]:
                    beste = (schluessel, k)
    if beste is None:
        raise ValueError("Punkte erlauben keine Zuordnung (alle gleich?)")
    return beste[1]


def abweichung_px(soll, ist, breite, hoehe):
    """Abstand zweier normierter Punkte in Fensterpixeln."""
    return math.hypot((soll[0] - ist[0]) * breite, (soll[1] - ist[1]) * hoehe)


def schwelle_px(breite, hoehe):
    return SCHWELLE * math.hypot(breite, hoehe)

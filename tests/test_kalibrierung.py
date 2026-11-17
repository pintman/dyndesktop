"""Kalibrier-Mathematik, abgeglichen mit Kivys eigenem Quelltext."""
import ast
import itertools
import random
from pathlib import Path

import pytest

from inbetrieb.kalibrierung import (abweichung_px, bestimme, kette, regression,
                                     schwelle_px)

KREUZE = [(0.1, 0.1), (0.9, 0.1), (0.1, 0.9), (0.9, 0.9)]
STICHPROBEN = [(0.0, 0.0), (1.0, 1.0), (0.2, 0.7), (0.93, 0.05), (0.5, 0.5)]


def kivy_assign_coord(modul, rotation):
    """assign_coord aus dem installierten Kivy-Provider herauslösen."""
    import kivy.input.providers as prov
    quelle = (Path(prov.__file__).parent / f"{modul}.py").read_text()
    for knoten in ast.walk(ast.parse(quelle)):
        if isinstance(knoten, ast.FunctionDef) and knoten.name == "assign_coord":
            ns = {"rotation": rotation}
            exec(compile(ast.Module([knoten], []), modul, "exec"), ns)
            return ns["assign_coord"]
    raise AssertionError(f"assign_coord nicht in {modul}.py gefunden")


# --- 4.1 Kette gegen Kivy -------------------------------------------------

@pytest.mark.parametrize("modul", ["hidinput", "mtdev"])
@pytest.mark.parametrize("rot, ix, iy", list(itertools.product((0, 90, 180, 270), (0, 1), (0, 1))))
def test_kette_wie_kivy_provider(modul, rot, ix, iy):
    assign = kivy_assign_coord(modul, rot)
    for vx, vy in STICHPROBEN:
        punkt = {"x": 0.0, "y": 0.0}
        assign(punkt, vx, ix, "xy")         # Kivy: ABS_MT_POSITION_X
        assign(punkt, vy, iy, "yx")         # Kivy: ABS_MT_POSITION_Y (vy = 1 - normalize)
        assert kette(vx, vy, rot, ix, iy) == pytest.approx((punkt["x"], punkt["y"]))


def test_kette_wie_kivy_postproc():
    from kivy.config import Config
    from kivy.input.postproc.calibration import InputPostprocCalibration

    class Ereignis:
        device = "touch"
        def __init__(self, sx, sy):
            self.sx, self.sy, self.ud = sx, sy, {}

    Config.add_section("postproc:calibration")
    try:
        Config.set("postproc:calibration", "touch",
                   "xratio=1.2,yratio=0.9,xoffset=-0.05,yoffset=0.03")
        pp = InputPostprocCalibration()
    finally:
        Config.remove_section("postproc:calibration")
    for vx, vy in STICHPROBEN:
        e = Ereignis(*kette(vx, vy, 90, 1, 0))
        pp.process([("update", e)])
        assert kette(vx, vy, 90, 1, 0, 1.2, 0.9, -0.05, 0.03) == pytest.approx((e.sx, e.sy))


def test_kivy_vorgaben_unterscheiden_sich():
    """Grund für den expliziten Rohmodus: hidinput spiegelt Y per Vorgabe, mtdev nicht."""
    import kivy.input.providers as prov
    basis = Path(prov.__file__).parent
    assert "drs('invert_y', 1)" in (basis / "hidinput.py").read_text()
    assert "drs('invert_y', 0)" in (basis / "mtdev.py").read_text()


# --- 4.2 Ausrichtung ------------------------------------------------------

def pruefe(k, roh, soll=KREUZE):
    for (vx, vy), s in zip(roh, soll):
        assert k.anwenden(vx, vy) == pytest.approx(s, abs=1e-6)


def test_identitaet():
    k = bestimme(KREUZE, KREUZE)
    assert (k.rotation, k.invert_x, k.invert_y) == (0, 0, 0)
    assert (k.xratio, k.yratio) == pytest.approx((1, 1))
    assert (k.xoffset, k.yoffset) == pytest.approx((0, 0), abs=1e-9)


def test_gespiegeltes_y():
    roh = [(x, 1 - y) for x, y in KREUZE]
    k = bestimme(KREUZE, roh)
    assert (k.rotation, k.invert_x, k.invert_y) == (0, 0, 1)
    pruefe(k, roh)


def test_vertauschte_achsen():
    roh = [(y, x) for x, y in KREUZE]
    k = bestimme(KREUZE, roh)
    assert k.rotation in (90, 270)
    pruefe(k, roh)


def test_vertauscht_und_gespiegelt():
    roh = [(1 - y, x) for x, y in KREUZE]
    k = bestimme(KREUZE, roh)
    assert k.rotation in (90, 270)
    pruefe(k, roh)


def test_180_grad_kanonisch():
    roh = [(1 - x, 1 - y) for x, y in KREUZE]
    k = bestimme(KREUZE, roh)
    assert (k.rotation, k.invert_x, k.invert_y) == (180, 0, 0)   # nicht 0/1/1
    pruefe(k, roh)


@pytest.mark.parametrize("rot, ix, iy", list(itertools.product((0, 90, 180, 270), (0, 1), (0, 1))))
def test_alle_kombinationen_werden_gefunden(rot, ix, iy):
    """Rohpunkte so konstruieren, dass (rot, ix, iy) sie exakt auf die Kreuze abbildet."""
    raster = [(i / 20, j / 20) for i in range(21) for j in range(21)]
    abbildung = {kette(vx, vy, rot, ix, iy): (vx, vy) for vx, vy in raster}
    roh = [abbildung[min(abbildung, key=lambda p: abs(p[0] - x) + abs(p[1] - y))]
           for x, y in KREUZE]
    k = bestimme(KREUZE, roh)
    pruefe(k, roh)
    # kanonisch: (r, ix, iy) ≡ (r+180, 1-ix, 1-iy) → wenigste Spiegelungen, dann kleinste Drehung
    assert k.invert_x + k.invert_y < 2
    if k.invert_x + k.invert_y == 1:
        assert k.rotation in (0, 90)


# --- 4.3 Skalierung, Versatz, Fehler --------------------------------------

def test_rahmen_groesser_als_bild():
    roh = [(0.5 + (x - 0.5) * 0.8, 0.5 + (y - 0.5) * 0.9) for x, y in KREUZE]
    k = bestimme(KREUZE, roh)
    assert k.xratio > 1 and k.yratio > 1
    pruefe(k, roh)


def test_rahmen_kleiner_als_fenster():
    roh = [(0.48 + (x - 0.5) * 1.1, 0.5 + (y - 0.5) * 1.05) for x, y in KREUZE]
    k = bestimme(KREUZE, roh)
    assert k.xratio < 1 and k.yratio < 1
    pruefe(k, roh)


def test_rauschen():
    rnd = random.Random(3)
    roh = [(0.02 + x * 0.95 + rnd.uniform(-0.004, 0.004),
            1 - (0.03 + y * 0.9) + rnd.uniform(-0.004, 0.004)) for x, y in KREUZE]
    k = bestimme(KREUZE, roh)
    assert (k.rotation, k.invert_x, k.invert_y) == (0, 0, 1)
    breite, hoehe = 1600, 900
    for (vx, vy), s in zip(roh, KREUZE):
        assert abweichung_px(s, k.anwenden(vx, vy), breite, hoehe) < schwelle_px(breite, hoehe)
    # Kontrollkreuz Mitte, gleiches Gerätemodell
    mitte = k.anwenden(0.02 + 0.5 * 0.95, 1 - (0.03 + 0.5 * 0.9))
    assert abweichung_px((0.5, 0.5), mitte, breite, hoehe) < schwelle_px(breite, hoehe)


def test_fehlberuehrung_ueber_schwelle():
    k = bestimme(KREUZE, KREUZE)
    breite, hoehe = 1920, 1080
    daneben = k.anwenden(0.6, 0.55)
    assert abweichung_px((0.5, 0.5), daneben, breite, hoehe) > schwelle_px(breite, hoehe)


def test_fehlerfunktion_pixel():
    assert abweichung_px((0.5, 0.5), (0.6, 0.5), 1000, 500) == pytest.approx(100)
    assert schwelle_px(1600, 1200) == pytest.approx(40)


def test_regression():
    assert regression([0, 1, 2], [1, 3, 5])[:2] == pytest.approx((2, 1))
    assert regression([1, 1, 1], [0, 1, 2]) is None


def test_zu_wenige_oder_gleiche_punkte():
    with pytest.raises(ValueError):
        bestimme(KREUZE[:2], KREUZE[:2])
    with pytest.raises(ValueError):
        bestimme(KREUZE, [(0.5, 0.5)] * 4)

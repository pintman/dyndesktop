"""Touchtest-Bericht: Datei, Felder, Name mit Zeitstempel."""
import json
import re
from datetime import datetime

from inbetrieb.bericht import Bericht, bericht_ordner


def test_speichern(tmp_path):
    b = Bericht(geraet="hidinput,/dev/input/by-id/x", fenster=(1600, 900), maximum=5,
                doppelte_ereignisse=2)
    b.heatmap[0][0] = 3
    b.heatmap[8][15] = 1
    b.geistertouches.append({"dauer_s": 60, "anzahl": 1, "positionen": [[10, 20]]})
    b.abweichungen += [{"ziel": [80, 45], "ist": [83, 49], "px": 5.0},
                       {"ziel": [800, 450], "ist": [800, 452], "px": 2.0}]
    pfad = b.speichern(tmp_path, jetzt=datetime(2026, 11, 17, 9, 5, 7))

    assert pfad == tmp_path / "touchtest-20261117-090507.json"
    d = json.loads(pfad.read_text())
    for feld in ("geraet", "fenster", "maximum", "raster", "heatmap", "abdeckung",
                 "geistertouches", "geistertouches_gesamt", "abweichungen",
                 "max_abweichung", "doppelte_ereignisse", "zeitpunkt"):
        assert feld in d, feld
    assert d["maximum"] == 5
    assert d["abdeckung"] == round(2 / 144, 4)
    assert d["max_abweichung"] == 5.0
    assert d["geistertouches_gesamt"] == 1
    assert d["zeitpunkt"] == "2026-11-17T09:05:07"


def test_standardordner(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    assert bericht_ordner() == tmp_path / "dyndesktop"
    pfad = Bericht().speichern()
    assert pfad.parent == tmp_path / "dyndesktop"
    assert re.fullmatch(r"touchtest-\d{8}-\d{6}\.json", pfad.name)
    assert json.loads(pfad.read_text())["max_abweichung"] is None


def test_standardordner_ohne_xdg(monkeypatch, tmp_path):
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert bericht_ordner() == tmp_path / ".local/state/dyndesktop"

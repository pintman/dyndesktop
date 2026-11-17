"""niri-Konfiguration: Vorlage, struts, Ausgänge, CLI, niri validate."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from inbetrieb import niriconfig as nc

PROJEKT = Path(__file__).resolve().parent.parent


def drm(root, *namen):
    d = root / "sys/class/drm"
    d.mkdir(parents=True)
    for n in ("card0", "renderD128", "version", *namen):
        (d / n).mkdir()
    return root


@pytest.fixture
def laptop(tmp_path):
    return drm(tmp_path / "laptop", "card0-eDP-1", "card0-HDMI-A-1", "card0-Writeback-1")


@pytest.fixture
def nuc(tmp_path):
    return drm(tmp_path / "nuc", "card0-HDMI-A-1", "card0-DP-1", "card0-DP-2")


# --- 3.4 Vorlage ----------------------------------------------------------

def test_vorlage_inhalt():
    t = nc.erzeugen("/home/pi/dyndesktop")
    for erwartet in ("gaps 0", "focus-ring {\n        off", "border {\n        off",
                     "open-maximized true", "prefer-no-csd", "touch {\n        off",
                     "hide-after-inactive-ms", 'background-color "#000000"',
                     'spawn-at-startup "/home/pi/dyndesktop/kiosk.sh"', "skip-at-startup"):
        assert erwartet in t, erwartet
    assert nc.lese_struts(t) == {"left": 0, "right": 0, "top": 0, "bottom": 0}


def test_ohne_datei_struts_null(tmp_path, nuc):
    pfad = tmp_path / "niri/config.kdl"
    assert nc.schreiben(PROJEKT, pfad, nuc) is True
    assert nc.struts_lesen(pfad) == dict.fromkeys(nc.KANTEN, 0)
    assert not (tmp_path / "niri/config.kdl.bak").exists()


def test_struts_bleiben_beim_neuschreiben(tmp_path, nuc):
    pfad = tmp_path / "config.kdl"
    nc.schreiben(PROJEKT, pfad, nuc)
    nc.struts_setzen({"left": 120, "top": 33.5, "bottom": 7}, pfad)
    pfad.write_text(pfad.read_text().replace("gaps 0", "gaps 16"))   # Handänderung
    alt = pfad.read_text()

    assert nc.schreiben(PROJEKT, pfad, nuc) is True
    assert nc.struts_lesen(pfad) == {"left": 120, "right": 0, "top": 33.5, "bottom": 7}
    assert "gaps 0" in pfad.read_text()
    assert (tmp_path / "config.kdl.bak").read_text() == alt
    assert nc.schreiben(PROJEKT, pfad, nuc) is False                  # zweiter Lauf: nichts


# --- 3.5 Ausgänge ---------------------------------------------------------

def test_laptop_intern_aus(laptop):
    intern, extern = nc.ausgaenge(laptop)
    assert intern == ["eDP-1"]
    assert extern == ["HDMI-A-1"]
    t = nc.erzeugen(PROJEKT, intern=intern, extern=extern)
    assert 'output "eDP-1" {\n    off\n}' in t
    assert 'output "HDMI-A-1" {\n    scale 1\n}' in t


def test_nuc_nur_hdmi(nuc):
    intern, extern = nc.ausgaenge(nuc)
    assert intern == []
    assert extern == ["DP-1", "DP-2", "HDMI-A-1"]
    assert "off\n}" not in nc.erzeugen(PROJEKT, intern=intern, extern=extern).split("layout")[0]


# --- 3.6 struts setzen/lesen + CLI ----------------------------------------

def test_struts_setzen_ohne_datei(tmp_path):
    with pytest.raises(FileNotFoundError):
        nc.struts_setzen({"left": 1}, tmp_path / "fehlt.kdl")


def test_cli_gegen_xdg_config_home(tmp_path, laptop):
    env = {**os.environ, "XDG_CONFIG_HOME": str(tmp_path / "cfg")}
    lauf = lambda *a: subprocess.run([sys.executable, "-m", "inbetrieb.niriconfig", *a],
                                     cwd=PROJEKT, env=env, capture_output=True, text=True)
    r = lauf("schreiben", str(PROJEKT), "--root", str(laptop))
    assert r.returncode == 0, r.stderr
    pfad = tmp_path / "cfg/niri/config.kdl"
    assert 'output "eDP-1"' in pfad.read_text()
    nc.struts_setzen({"right": 42}, pfad)
    assert "unverändert" in lauf("schreiben", str(PROJEKT), "--root", str(laptop)).stdout
    assert lauf("struts").stdout.strip() == "left=0 right=42 top=0 bottom=0"


@pytest.mark.skipif(not shutil.which("niri"), reason="niri nicht installiert")
def test_niri_validate(tmp_path, laptop):
    pfad = tmp_path / "config.kdl"
    nc.schreiben(PROJEKT, pfad, laptop)
    nc.struts_setzen({"left": 10, "top": 2.5}, pfad)
    r = subprocess.run(["niri", "validate", "-c", str(pfad)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr

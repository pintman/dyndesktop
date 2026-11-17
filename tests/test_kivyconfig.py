"""config.ini gezielt ändern: Eingabe, Kalibrierung, Sicherung, CLI, Rohmodus."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from inbetrieb import kivyconfig as kc

PROJEKT = Path(__file__).resolve().parent.parent
PFAD = "/dev/input/by-id/usb-LM-event-if00"

KIVY_DEFAULT = """\
[kivy]
keyboard_repeat_delay = 300
log_name = kivy_%y-%m-%d_%_.txt
config_version = 27

[input]
mouse = mouse
%(name)s = probesysfs

[postproc]
double_tap_time = 250

[modules]

"""


@pytest.fixture
def ini(tmp_path):
    p = tmp_path / "config.ini"
    p.write_text(KIVY_DEFAULT)
    return p


def test_eingabe_setzen(ini):
    cfg = kc.setze_eingabe(kc.lesen(ini), PFAD, "hidinput")
    assert cfg.get("input", "touch") == f"hidinput,{PFAD}"
    assert cfg.get("input", "mouse") == "mouse,disable_on_activity"
    assert not cfg.has_option("input", "%(name)s")          # kein doppeltes Öffnen
    assert cfg.get("kivy", "log_name") == "kivy_%y-%m-%d_%_.txt"   # fremd, mit %
    assert cfg.get("postproc", "double_tap_time") == "250"


def test_ausrichtung_bleibt_bei_neuem_pfad(ini):
    cfg = kc.lesen(ini)
    cfg.set("input", "touch", "hidinput,/dev/input/event5,rotation=90,invert_x=1,min_position_x=200")
    kc.setze_eingabe(cfg, PFAD, "mtdev")
    assert kc.eingabe(cfg) == ("mtdev", PFAD, {"rotation": "90", "invert_x": "1",
                                                "min_position_x": "200"})


def test_kalibrierung_bleibt_beim_erneuten_schreiben(ini):
    cfg = kc.setze_eingabe(kc.lesen(ini), PFAD, "hidinput")
    kc.setze_kalibrierung(cfg, 180, 0, 1, 1.02, 0.98, -0.01, 0.015)
    kc.schreiben(cfg, ini)
    vorher = ini.read_text()

    cfg2 = kc.setze_eingabe(kc.lesen(ini), PFAD, "hidinput")
    assert kc.schreiben(cfg2, ini) is False                  # nichts geändert
    assert ini.read_text() == vorher
    assert kc.lesen(ini).get("postproc:calibration", "touch") == \
        "xratio=1.020000,yratio=0.980000,xoffset=-0.010000,yoffset=0.015000"


def test_kalibrierung_schreiben_mit_sicherung(ini):
    cfg = kc.setze_eingabe(kc.lesen(ini), PFAD, "hidinput")
    kc.schreiben(cfg, ini)
    alt = ini.read_text()
    kc.setze_kalibrierung(cfg, 90, 1, 0, 1.1, 0.9, 0.05, -0.05)
    assert kc.schreiben(cfg, ini) is True
    assert (ini.parent / "config.ini.bak").read_text() == alt
    neu = kc.lesen(ini)
    assert kc.eingabe(neu)[2] == {"rotation": "90", "invert_x": "1", "invert_y": "0"}
    assert neu.get("postproc:calibration", "touch").startswith("xratio=1.100000,")


def test_kalibrierung_ohne_eingabe(ini):
    with pytest.raises(ValueError):
        kc.setze_kalibrierung(kc.lesen(ini), 0, 0, 0, 1, 1, 0, 0)


def test_rohmodus(ini):
    cfg = kc.setze_eingabe(kc.lesen(ini), PFAD, "hidinput")
    kc.setze_kalibrierung(cfg, 270, 1, 1, 1.1, 1.1, 0, 0)
    kc.rohmodus(cfg)
    assert not cfg.has_section("postproc:calibration")
    assert kc.eingabe(cfg)[2] == {"rotation": "0", "invert_x": "0", "invert_y": "0"}


def test_rohmodus_auf_kivy_config():
    """Der Rohmodus muss auf Kivys eigenem Config-Objekt funktionieren."""
    from kivy.config import ConfigParser
    cfg = ConfigParser(name="rohtest")
    cfg.read_string(f"[input]\ntouch = hidinput,{PFAD},invert_y=1\n"
                    "[postproc:calibration]\ntouch = xratio=2\n")
    kc.rohmodus(cfg)
    assert cfg.get("input", "touch") == f"hidinput,{PFAD},invert_y=0,rotation=0,invert_x=0"
    assert not cfg.has_section("postproc:calibration")


def test_cli_gegen_kivy_home(tmp_path):
    (tmp_path / "config.ini").write_text(KIVY_DEFAULT)
    env = {**os.environ, "KIVY_HOME": str(tmp_path)}
    lauf = lambda: subprocess.run([sys.executable, "-m", "inbetrieb.kivyconfig", "input", PFAD, "mtdev"],
                                  cwd=PROJEKT, env=env, capture_output=True, text=True)
    r = lauf()
    assert r.returncode == 0, r.stderr
    assert "geschrieben" in r.stdout
    assert kc.lesen(tmp_path / "config.ini").get("input", "touch") == f"mtdev,{PFAD}"
    assert "unverändert" in lauf().stdout


def test_cli_ohne_datei(tmp_path):
    env = {**os.environ, "KIVY_HOME": str(tmp_path / "neu")}
    r = subprocess.run([sys.executable, "-m", "inbetrieb.kivyconfig", "input", PFAD, "hidinput"],
                       cwd=PROJEKT, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "neu/config.ini").exists()

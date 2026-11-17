"""Geräteerkennung gegen Fixture-Verzeichnisse (sysfs + /dev/input)."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from inbetrieb import geraet
from inbetrieb.geraet import (ABS_MT_POSITION_X, ABS_MT_SLOT, ABS_X, ABS_Y,
                              INPUT_PROP_DIRECT, INPUT_PROP_POINTER, parse_bitmaske)

PROJEKT = Path(__file__).resolve().parent.parent

TYP_B = {ABS_X, ABS_Y, ABS_MT_SLOT, ABS_MT_POSITION_X, 0x36, 0x39}
TYP_A = {ABS_X, ABS_Y, ABS_MT_POSITION_X, 0x36}
SINGLE = {ABS_X, ABS_Y}


def maske(bits, wortbreite=geraet.BITS_PRO_WORT):
    if not bits:
        return "0"
    n = max(bits) // wortbreite + 1
    worte = [sum(1 << (b % wortbreite) for b in bits if b // wortbreite == i) for i in range(n)]
    return " ".join(f"{w:x}" for w in reversed(worte))


def lege_an(root, event, name, abs_bits, props=(), by_id=None, by_path=None):
    dev = root / "sys/class/input" / event / "device"
    (dev / "capabilities").mkdir(parents=True)
    (dev / "capabilities/abs").write_text(maske(set(abs_bits)) + "\n")
    (dev / "properties").write_text(maske(set(props)) + "\n")
    (dev / "name").write_text(name + "\n")
    for unter, link in (("by-id", by_id), ("by-path", by_path)):
        if link:
            d = root / "dev/input" / unter
            d.mkdir(parents=True, exist_ok=True)
            (d / link).symlink_to(f"../{event}")


# --- 2.1 Bitmaske ---------------------------------------------------------

def test_bitmaske_64bit_realer_wert():
    assert parse_bitmaske("660800000000003", 64) == {0, 1, 0x2F, 0x35, 0x36, 0x39, 0x3A}


def test_bitmaske_32bit_mehrere_worte():
    assert parse_bitmaske("2608000 3", 32) == {0, 1, 0x2F, 0x35, 0x36, 0x39}


def test_bitmaske_null():
    assert parse_bitmaske("0") == set()


@pytest.mark.parametrize("bits, typ", [(TYP_B, "B"), (TYP_A, "A"), (SINGLE, "single")])
def test_typ(tmp_path, bits, typ):
    lege_an(tmp_path, "event3", "Rahmen", bits, {INPUT_PROP_DIRECT})
    g = geraet.kandidaten(tmp_path)[0]
    assert g.typ == typ
    assert g.faehigkeiten.direct
    assert g.provider == ("mtdev" if typ == "A" else "hidinput")


def test_touchpad_wird_ignoriert(tmp_path):
    lege_an(tmp_path, "event4", "Touchpad", TYP_B, {INPUT_PROP_POINTER})
    assert geraet.kandidaten(tmp_path) == []


def test_ohne_position_ignoriert(tmp_path):
    lege_an(tmp_path, "event1", "Power Button", set())
    assert geraet.kandidaten(tmp_path) == []


# --- 2.2 Pfad -------------------------------------------------------------

def test_by_id_bevorzugt(tmp_path):
    lege_an(tmp_path, "event5", "Rahmen", TYP_B, {INPUT_PROP_DIRECT},
            by_id="usb-LM_Touch-event-if00", by_path="pci-0000:00:14.0-usb-0:1:1.0-event")
    g = geraet.finde(tmp_path)
    assert g.pfad == "/dev/input/by-id/usb-LM_Touch-event-if00"
    assert g.warnungen == []


def test_by_path_als_rueckfall(tmp_path):
    lege_an(tmp_path, "event5", "Rahmen", TYP_B, {INPUT_PROP_DIRECT},
            by_path="pci-0000:00:14.0-usb-0:1:1.0-event")
    g = geraet.finde(tmp_path)
    assert g.pfad == "/dev/input/by-path/pci-0000:00:14.0-usb-0:1:1.0-event"
    assert any("by-path" in w for w in g.warnungen)


def test_eventx_mit_warnung(tmp_path):
    lege_an(tmp_path, "event5", "Rahmen", TYP_B, {INPUT_PROP_DIRECT})
    g = geraet.finde(tmp_path)
    assert g.pfad == "/dev/input/event5"
    assert any("kein stabiler Pfad" in w for w in g.warnungen)


def test_mehrere_kandidaten_direct_zuerst(tmp_path):
    lege_an(tmp_path, "event2", "Grafiktablett", SINGLE, by_id="usb-Tablet-event-mouse")
    lege_an(tmp_path, "event7", "Rahmen", TYP_B, {INPUT_PROP_DIRECT}, by_id="usb-Rahmen-event-if00")
    lege_an(tmp_path, "event9", "Zweiter Rahmen", TYP_A, {INPUT_PROP_DIRECT})
    g = geraet.finde(tmp_path)
    assert g.event == "event7"
    assert any("event9" in w for w in g.warnungen)
    assert any("event2" in w for w in g.warnungen)


def test_single_touch_warnung(tmp_path):
    lege_an(tmp_path, "event5", "Rahmen", SINGLE, {INPUT_PROP_DIRECT}, by_id="usb-R-event-if00")
    assert any("nur Single-Touch" in w for w in geraet.finde(tmp_path).warnungen)


# --- 2.3 CLI --------------------------------------------------------------

def cli(*args):
    return subprocess.run([sys.executable, "-m", "inbetrieb.geraet", *args],
                          cwd=PROJEKT, capture_output=True, text=True)


def test_cli_mit_geraet(tmp_path):
    lege_an(tmp_path, "event5", "LM Touch", TYP_A, {INPUT_PROP_DIRECT}, by_id="usb-LM-event-if00")
    r = cli("--root", str(tmp_path))
    assert r.returncode == 0
    werte = dict(z.split("=", 1) for z in r.stdout.splitlines())
    assert werte["PFAD"] == "/dev/input/by-id/usb-LM-event-if00"
    assert werte["PROVIDER"] == "mtdev"
    assert werte["TYP"] == "A"
    assert werte["NAME"] == "'LM Touch'"


def test_cli_ausgabe_ist_shell_tauglich(tmp_path):
    lege_an(tmp_path, "event5", "Rahmen $(boese)", SINGLE, {INPUT_PROP_DIRECT})
    r = cli("--root", str(tmp_path))
    sh = subprocess.run(["bash", "-c", 'eval "$1"; printf "%s|%s" "$NAME" "$TYP"', "_", r.stdout],
                        capture_output=True, text=True)
    assert sh.stdout == "Rahmen $(boese)|single"


def test_cli_ohne_geraet(tmp_path):
    (tmp_path / "sys/class/input").mkdir(parents=True)
    r = cli("--root", str(tmp_path))
    assert r.returncode == 1
    assert r.stdout == ""

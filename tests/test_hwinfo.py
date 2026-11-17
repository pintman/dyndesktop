"""Hardware-Übersicht gegen Fixture-Verzeichnisse, Achsen per Fake-Leser."""
import json

from inbetrieb import hwinfo
from inbetrieb.geraet import INPUT_PROP_DIRECT, INPUT_PROP_POINTER

from .test_geraet import SINGLE, TYP_B, lege_an


def ergaenze_ids(root, event, bus="0003", vendor="1ff7", product="0f0d", phys="usb-0000:00:14.0-1/input0"):
    dev = root / "sys/class/input" / event / "device"
    (dev / "id").mkdir()
    for k, v in (("bustype", bus), ("vendor", vendor), ("product", product)):
        (dev / "id" / k).write_text(v + "\n")
    (dev / "phys").write_text(phys + "\n")


def achse(mn, mx, res=0):
    return {"wert": 0, "min": mn, "max": mx, "fuzz": 0, "flat": 0, "aufloesung": res}


def fake_leser(werte):
    def leser(pfad, codes):
        return {c: werte[c] for c in codes if c in werte}
    return leser


B_ACHSEN = {0x00: achse(0, 32767, 100), 0x01: achse(0, 32767, 200),
            0x2F: achse(0, 9), 0x35: achse(0, 32767, 100), 0x36: achse(0, 32767, 200),
            0x39: achse(0, 65535)}


def test_rahmen_vollstaendig(tmp_path):
    lege_an(tmp_path, "event5", "LM Touch", TYP_B, {INPUT_PROP_DIRECT}, by_id="usb-LM-event-if00")
    ergaenze_ids(tmp_path, "event5")
    [i] = hwinfo.sammle(tmp_path, fake_leser(B_ACHSEN))
    assert (i.bus, i.vendor, i.product) == ("USB", "1ff7", "0f0d")
    assert i.typ == "B" and i.direct and i.gewaehlt
    assert i.slots == 10
    assert i.groesse_mm == (327.7, 163.8)
    assert i.pfad == "/dev/input/by-id/usb-LM-event-if00"
    assert i.kivy_input() == ("hidinput,/dev/input/by-id/usb-LM-event-if00,min_position_x=0,"
                              "max_position_x=32767,min_position_y=0,max_position_y=32767")


def test_touchpad_gelistet_aber_nicht_gewaehlt(tmp_path):
    lege_an(tmp_path, "event3", "Touchpad", TYP_B, {INPUT_PROP_POINTER})
    lege_an(tmp_path, "event5", "Rahmen", TYP_B, {INPUT_PROP_DIRECT})
    infos = hwinfo.sammle(tmp_path, fake_leser(B_ACHSEN))
    assert [(i.event, i.touchpad, i.gewaehlt) for i in infos] == [
        ("event3", True, False), ("event5", False, True)]
    assert "Kivy:" not in hwinfo.als_text(infos[:1])


def test_bus_unbekannt_und_i2c(tmp_path):
    lege_an(tmp_path, "event1", "A", SINGLE, {INPUT_PROP_DIRECT})
    ergaenze_ids(tmp_path, "event1", bus="0018")
    lege_an(tmp_path, "event2", "B", SINGLE, {INPUT_PROP_DIRECT})
    ergaenze_ids(tmp_path, "event2", bus="00ab")
    infos = hwinfo.sammle(tmp_path, fake_leser({}))
    assert [i.bus for i in infos] == ["I2C", "0x00ab"]


def test_ohne_aufloesung_keine_groesse(tmp_path):
    lege_an(tmp_path, "event1", "Single", SINGLE, {INPUT_PROP_DIRECT})
    [i] = hwinfo.sammle(tmp_path, fake_leser({0x00: achse(200, 3900), 0x01: achse(250, 3850)}))
    assert i.groesse_mm is None and i.slots is None
    assert "min_position_x=200" in i.kivy_input()


def test_fehlende_rechte(tmp_path):
    lege_an(tmp_path, "event5", "Rahmen", TYP_B, {INPUT_PROP_DIRECT})

    def verweigert(pfad, codes):
        raise PermissionError(13, "Permission denied")

    [i] = hwinfo.sammle(tmp_path, verweigert)
    assert i.achsen == {} and i.kivy_input() is None
    assert "Gruppe input" in i.hinweise[0]


def test_eviocgabs_wert():
    assert hwinfo.eviocgabs(0x35) == 0x80184575       # wie linux/input.h


def test_cli_json_und_leer(tmp_path, capsys, monkeypatch):
    assert hwinfo.main(["--root", str(tmp_path)]) == 1
    lege_an(tmp_path, "event5", "Rahmen", TYP_B, {INPUT_PROP_DIRECT})
    monkeypatch.setattr(hwinfo, "lies_achsen", fake_leser(B_ACHSEN))
    monkeypatch.setattr(hwinfo.sammle, "__defaults__", ("/", fake_leser(B_ACHSEN)))
    capsys.readouterr()
    assert hwinfo.main(["--json", "--root", str(tmp_path)]) == 0
    daten = json.loads(capsys.readouterr().out)
    assert daten[0]["slots"] == 10 and daten[0]["kivy_input"].startswith("hidinput,")
    assert hwinfo.main(["--root", str(tmp_path)]) == 0
    assert "event5: Rahmen  ← von setup.sh gewählt" in capsys.readouterr().out

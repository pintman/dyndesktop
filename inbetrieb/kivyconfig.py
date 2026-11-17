"""~/.kivy/config.ini gezielt ändern (D4). Nur Standardbibliothek.

CLI: python3 -m inbetrieb.kivyconfig input <pfad> <provider>
     python3 -m inbetrieb.kivyconfig zeigen
"""
import argparse
import configparser
import io
import os
import shutil
import sys
from pathlib import Path

GERAET = "touch"                       # Schlüssel in [input] und [postproc:calibration]
MAUS = "mouse,disable_on_activity"
KALIBRIER = "postproc:calibration"
AUSRICHTUNG = ("rotation", "invert_x", "invert_y")


def config_pfad():
    home = os.environ.get("KIVY_HOME")
    return Path(home) / "config.ini" if home else Path.home() / ".kivy" / "config.ini"


def lesen(pfad=None):
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.optionxform = str
    pfad = Path(pfad or config_pfad())
    if pfad.exists():
        cfg.read(pfad, encoding="utf-8")
    return cfg


def _text(cfg):
    buf = io.StringIO()
    cfg.write(buf)
    return buf.getvalue()


def schreiben(cfg, pfad=None):
    """Schreibt nur bei Änderung; vorher Sicherung config.ini.bak. True, wenn geschrieben."""
    pfad = Path(pfad or config_pfad())
    neu = _text(cfg)
    if pfad.exists():
        if pfad.read_text(encoding="utf-8") == neu:
            return False
        shutil.copy2(pfad, pfad.with_name(pfad.name + ".bak"))
    pfad.parent.mkdir(parents=True, exist_ok=True)
    tmp = pfad.with_name(pfad.name + ".tmp")
    tmp.write_text(neu, encoding="utf-8")
    tmp.replace(pfad)
    return True


# --- [input] touch = provider,pfad,key=wert,... -----------------------------

def parse_eingabe(wert):
    """'hidinput,/dev/x,rotation=90' → ('hidinput', '/dev/x', {'rotation': '90'})."""
    teile = [t.strip() for t in wert.split(",")]
    provider, pfad, params = teile[0], "", {}
    for t in teile[1:]:
        if "=" in t:
            k, v = t.split("=", 1)
            params[k.strip()] = v.strip()
        elif t and not pfad:
            pfad = t
    return provider, pfad, params


def format_eingabe(provider, pfad, params):
    return ",".join([provider, pfad, *(f"{k}={v}" for k, v in params.items())])


def eingabe(cfg):
    """(provider, pfad, params) des Touch-Eintrags oder None."""
    if cfg.has_option("input", GERAET):
        return parse_eingabe(cfg.get("input", GERAET))
    return None


def setze_eingabe(cfg, pfad, provider):
    """[input] touch + mouse setzen. Parameter (rotation/invert, Bereiche) eines
    bestehenden Eintrags bleiben, [postproc:calibration] und fremde Schlüssel auch.

    Einträge mit probesysfs fallen weg: sie öffnen dasselbe Gerät ein zweites Mal
    und erzeugen doppelte Touches.
    """
    if not cfg.has_section("input"):
        cfg.add_section("input")
    alt = eingabe(cfg)
    params = alt[2] if alt else {}
    cfg.set("input", GERAET, format_eingabe(provider, pfad, params))
    cfg.set("input", "mouse", MAUS)
    for k, v in list(cfg.items("input")):
        if v.split(",")[0].strip() == "probesysfs":
            cfg.remove_option("input", k)
    return cfg


def setze_kalibrierung(cfg, rotation, invert_x, invert_y, xratio, yratio, xoffset, yoffset):
    """Ausrichtung in [input] touch, Skalierung/Versatz in [postproc:calibration]."""
    alt = eingabe(cfg)
    if alt is None:
        raise ValueError("kein [input] touch-Eintrag – zuerst setup.sh ausführen")
    provider, pfad, params = alt
    params.update(rotation=str(int(rotation)), invert_x=str(int(bool(invert_x))),
                  invert_y=str(int(bool(invert_y))))
    cfg.set("input", GERAET, format_eingabe(provider, pfad, params))
    if not cfg.has_section(KALIBRIER):
        cfg.add_section(KALIBRIER)
    cfg.set(KALIBRIER, GERAET, f"xratio={xratio:.6f},yratio={yratio:.6f},"
                               f"xoffset={xoffset:.6f},yoffset={yoffset:.6f}")
    return cfg


def rohmodus(cfg):
    """Im Speicher (z. B. kivy.config.Config): Kalibrierung entfernen, Ausrichtung
    explizit neutral (hidinput hätte sonst invert_y=1 als Vorgabe) (D5)."""
    if cfg.has_section(KALIBRIER):
        cfg.remove_section(KALIBRIER)
    if cfg.has_option("input", GERAET):
        provider, pfad, params = parse_eingabe(cfg.get("input", GERAET))
        params.update(rotation="0", invert_x="0", invert_y="0")
        cfg.set("input", GERAET, format_eingabe(provider, pfad, params))
    return cfg


def main(argv=None):
    p = argparse.ArgumentParser(prog="python3 -m inbetrieb.kivyconfig")
    sub = p.add_subparsers(dest="befehl", required=True)
    e = sub.add_parser("input", help="Touch-Eingabe eintragen")
    e.add_argument("pfad")
    e.add_argument("provider", choices=["hidinput", "mtdev"])
    sub.add_parser("zeigen", help="Touch-Eintrag und Kalibrierung ausgeben")
    args = p.parse_args(argv)

    pfad = config_pfad()
    cfg = lesen(pfad)
    if args.befehl == "input":
        geaendert = schreiben(setze_eingabe(cfg, args.pfad, args.provider), pfad)
        print(f"{pfad}: {'geschrieben' if geaendert else 'unverändert'}")
    else:
        print("touch =", cfg.get("input", GERAET, fallback="-"))
        print("kalibrierung =", cfg.get(KALIBRIER, GERAET, fallback="-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""~/.config/niri/config.kdl erzeugen, struts lesen/setzen (D9, D12). Nur Standardbibliothek.

Die Datei gehört dem Skript. Beim Neuschreiben bleiben nur die struts erhalten.
Optionsnamen geprüft gegen niri v26.04.

CLI: python3 -m inbetrieb.niriconfig schreiben <projekt>
     python3 -m inbetrieb.niriconfig struts
"""
import argparse
import os
import re
import shutil
import sys
from pathlib import Path

KANTEN = ("left", "right", "top", "bottom")
INTERN = ("eDP", "LVDS", "DSI")

_STRUTS_BLOCK = re.compile(r"struts\s*\{([^}]*)\}")
_STRUT = re.compile(r"\b(left|right|top|bottom)\s+(-?\d+(?:\.\d+)?)")

VORLAGE = """\
// Erzeugt von dyndesktop (inbetrieb/niriconfig.py) – wird von setup.sh
// überschrieben. Nur die struts (Rahmenfläche) bleiben erhalten.
// Rückweg: config.kdl.bak

input {{
    // Touch liest Kivy selbst (hidinput/mtdev), niri soll ihn nicht verarbeiten.
    touch {{
        off
    }}
}}

cursor {{
    hide-when-typing
    hide-after-inactive-ms 1000
}}

{ausgaenge}
layout {{
    gaps 0
    background-color "#000000"
    // Rahmenfläche in logischen Pixeln (= Beamerpixel bei scale 1)
    struts {{
        left {left}
        right {right}
        top {top}
        bottom {bottom}
    }}
    focus-ring {{
        off
    }}
    border {{
        off
    }}
}}

window-rule {{
    open-maximized true
}}

prefer-no-csd

animations {{
    off
}}

gestures {{
    hot-corners {{
        off
    }}
}}

hotkey-overlay {{
    skip-at-startup
}}

spawn-at-startup "{kiosk}"

binds {{
    Mod+Shift+E {{ quit; }}
}}
"""


def config_pfad():
    basis = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
    return Path(basis) / "niri" / "config.kdl"


def _zahl(text):
    f = float(text)
    return int(f) if f.is_integer() else f


def lese_struts(text):
    """struts aus config.kdl-Text, fehlende Kanten 0."""
    werte = dict.fromkeys(KANTEN, 0)
    m = _STRUTS_BLOCK.search(text or "")
    if m:
        for kante, wert in _STRUT.findall(m.group(1)):
            werte[kante] = _zahl(wert)
    return werte


def ausgaenge(root="/"):
    """(interne, externe) Ausgänge aus /sys/class/drm/card*-<name>."""
    intern, extern = [], []
    for p in sorted((Path(root) / "sys/class/drm").glob("card*-*")):
        name = p.name.split("-", 1)[1]
        if name.startswith("Writeback"):
            continue
        (intern if name.startswith(INTERN) else extern).append(name)
    return intern, extern


def _kdl_str(s):
    return str(s).replace("\\", "\\\\").replace('"', '\\"')


def erzeugen(projekt, struts=None, intern=(), extern=()):
    s = dict.fromkeys(KANTEN, 0) | (struts or {})
    bloecke = [f'output "{_kdl_str(n)}" {{\n    off\n}}\n' for n in intern]
    bloecke += [f'output "{_kdl_str(n)}" {{\n    scale 1\n}}\n' for n in extern]
    return VORLAGE.format(ausgaenge="\n".join(bloecke),
                          kiosk=_kdl_str(Path(projekt) / "kiosk.sh"), **s)


def _schreibe_atomar(pfad, text):
    pfad.parent.mkdir(parents=True, exist_ok=True)
    tmp = pfad.with_name(pfad.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(pfad)


def sichern(pfad=None):
    pfad = Path(pfad or config_pfad())
    if pfad.exists():
        shutil.copy2(pfad, pfad.with_name(pfad.name + ".bak"))


def schreiben(projekt, pfad=None, root="/"):
    """config.kdl aus Vorlage, struts aus bestehender Datei. True, wenn geändert."""
    pfad = Path(pfad or config_pfad())
    alt = pfad.read_text(encoding="utf-8") if pfad.exists() else None
    intern, extern = ausgaenge(root)
    neu = erzeugen(projekt, lese_struts(alt), intern, extern)
    if alt == neu:
        return False
    sichern(pfad)
    _schreibe_atomar(pfad, neu)
    return True


def struts_lesen(pfad=None):
    pfad = Path(pfad or config_pfad())
    return lese_struts(pfad.read_text(encoding="utf-8") if pfad.exists() else "")


def struts_setzen(struts, pfad=None):
    """Nur den struts-Block ersetzen (Flächen-Screen); ohne Sicherung – die legt
    der Flächen-Screen einmal beim Start an."""
    pfad = Path(pfad or config_pfad())
    text = pfad.read_text(encoding="utf-8")
    s = struts_lesen(pfad) | struts
    block = "struts {\n" + "".join(f"        {k} {s[k]}\n" for k in KANTEN) + "    }"
    neu, n = _STRUTS_BLOCK.subn(lambda _: block, text, count=1)
    if not n:
        raise ValueError(f"kein struts-Block in {pfad} – setup.sh ausführen")
    _schreibe_atomar(pfad, neu)


def main(argv=None):
    p = argparse.ArgumentParser(prog="python3 -m inbetrieb.niriconfig")
    sub = p.add_subparsers(dest="befehl", required=True)
    s = sub.add_parser("schreiben", help="config.kdl aus Vorlage erzeugen")
    s.add_argument("projekt", type=Path)
    s.add_argument("--root", default="/", help="Wurzel für /sys (Tests)")
    sub.add_parser("struts", help="struts ausgeben")
    args = p.parse_args(argv)

    pfad = config_pfad()
    if args.befehl == "schreiben":
        geaendert = schreiben(args.projekt.resolve(), pfad, args.root)
        print(f"{pfad}: {'geschrieben' if geaendert else 'unverändert'}")
    else:
        print(" ".join(f"{k}={v}" for k, v in struts_lesen(pfad).items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())

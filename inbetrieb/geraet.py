"""Touch-Gerät über sysfs finden (D3). Nur Standardbibliothek.

CLI: python3 -m inbetrieb.geraet [--root <verzeichnis>]
Ausgabe: Shell-Zuweisungen (PFAD, PROVIDER, TYP, NAME, WARNUNGEN), Exit 1 ohne Gerät.
"""
import argparse
import shlex
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path

ABS_X = 0x00
ABS_Y = 0x01
ABS_MT_SLOT = 0x2F
ABS_MT_POSITION_X = 0x35
INPUT_PROP_POINTER = 0x00
INPUT_PROP_DIRECT = 0x01

BITS_PRO_WORT = struct.calcsize("l") * 8


def parse_bitmaske(text, bits=BITS_PRO_WORT):
    """sysfs-Bitmaske ("1 0 7000003" – höchstwertiges Wort zuerst) → Menge gesetzter Bits."""
    gesetzt = set()
    for i, wort in enumerate(reversed(text.split())):
        wert = int(wort, 16)
        for b in range(bits):
            if wert >> b & 1:
                gesetzt.add(i * bits + b)
    return gesetzt


@dataclass
class Faehigkeiten:
    abs_bits: set
    prop_bits: set

    @property
    def multitouch(self):
        return ABS_MT_POSITION_X in self.abs_bits

    @property
    def typ(self):
        """'B' (Slots), 'A' (MT ohne Slots), 'single' (nur ABS_X/Y), None (keine Position)."""
        if self.multitouch:
            return "B" if ABS_MT_SLOT in self.abs_bits else "A"
        if {ABS_X, ABS_Y} <= self.abs_bits:
            return "single"
        return None

    @property
    def direct(self):
        return INPUT_PROP_DIRECT in self.prop_bits

    @property
    def touchpad(self):
        return INPUT_PROP_POINTER in self.prop_bits and not self.direct


def lies_faehigkeiten(event_dir):
    dev = Path(event_dir) / "device"
    abs_text = (dev / "capabilities" / "abs").read_text()
    try:
        prop_text = (dev / "properties").read_text()
    except FileNotFoundError:
        prop_text = "0"
    return Faehigkeiten(parse_bitmaske(abs_text), parse_bitmaske(prop_text))


@dataclass
class Geraet:
    event: str                     # z. B. "event5"
    name: str
    faehigkeiten: Faehigkeiten
    pfad: str = ""
    warnungen: list = field(default_factory=list)

    @property
    def typ(self):
        return self.faehigkeiten.typ

    @property
    def provider(self):
        return "mtdev" if self.typ == "A" else "hidinput"


def _event_nr(name):
    try:
        return int(name.removeprefix("event"))
    except ValueError:
        return 1 << 30


def kandidaten(root="/"):
    """Alle Touch-Geräte, Direct-Touch zuerst; Touchpads und Geräte ohne Position fallen weg."""
    basis = Path(root) / "sys/class/input"
    gefunden = []
    for ev in sorted(basis.glob("event*"), key=lambda p: _event_nr(p.name)):
        try:
            f = lies_faehigkeiten(ev)
        except (FileNotFoundError, ValueError):
            continue
        if f.typ is None or f.touchpad:
            continue
        try:
            name = (ev / "device" / "name").read_text().strip()
        except FileNotFoundError:
            name = ev.name
        gefunden.append(Geraet(ev.name, name, f))
    gefunden.sort(key=lambda g: not g.faehigkeiten.direct)   # stabil: Reihenfolge bleibt
    return gefunden


def stabiler_pfad(event, root="/"):
    """(Pfad, Warnung) – by-id, sonst by-path, sonst /dev/input/eventX mit Warnung."""
    dev = Path(root) / "dev/input"
    for unter in ("by-id", "by-path"):
        d = dev / unter
        if not d.is_dir():
            continue
        treffer = sorted(l.name for l in d.iterdir()
                         if l.is_symlink() and Path(l.readlink()).name == event)
        if treffer:
            # "-event-" bevorzugen (by-id kennt auch "-mouse"-Verweise auf andere Knoten)
            treffer.sort(key=lambda n: "-event-" not in n)
            warnung = None if unter == "by-id" else "kein by-id-Verweis, nutze by-path"
            return f"/dev/input/{unter}/{treffer[0]}", warnung
    return f"/dev/input/{event}", f"kein stabiler Pfad, nutze /dev/input/{event} (kann sich ändern)"


def finde(root="/"):
    """Bestes Touch-Gerät mit Pfad und Warnungen oder None."""
    alle = kandidaten(root)
    if not alle:
        return None
    g = alle[0]
    g.pfad, w = stabiler_pfad(g.event, root)
    if w:
        g.warnungen.append(w)
    if not g.faehigkeiten.direct:
        g.warnungen.append("Gerät meldet kein INPUT_PROP_DIRECT (evtl. kein Touchscreen)")
    if g.typ == "single":
        g.warnungen.append("nur Single-Touch: Gerät meldet keine Multitouch-Achsen")
    for weitere in alle[1:]:
        g.warnungen.append(f"weiteres Touch-Gerät ignoriert: {weitere.event} ({weitere.name})")
    return g


def main(argv=None):
    p = argparse.ArgumentParser(prog="python3 -m inbetrieb.geraet")
    p.add_argument("--root", default="/", help="Wurzel für sysfs/dev (Tests)")
    args = p.parse_args(argv)
    g = finde(args.root)
    if g is None:
        print("kein Touch-Gerät gefunden", file=sys.stderr)
        return 1
    werte = {"PFAD": g.pfad, "PROVIDER": g.provider, "TYP": g.typ,
             "NAME": g.name, "WARNUNGEN": "; ".join(g.warnungen)}
    for k, v in werte.items():
        print(f"{k}={shlex.quote(v)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

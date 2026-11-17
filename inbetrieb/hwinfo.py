"""Überblick über angeschlossene Touch-Hardware. Nur Standardbibliothek.

CLI: python3 -m inbetrieb.hwinfo [--json] [--root <verzeichnis>]
Zeigt alle Eingabegeräte mit Positionsachsen (auch Touchpads), IDs, Treiber,
Achsenbereiche (EVIOCGABS) und einen Vorschlag für Kivy-[input]. Exit 1 ohne Gerät.
"""
import argparse
import json
import os
import struct
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .geraet import (ABS_MT_POSITION_X, ABS_MT_SLOT, ABS_X, ABS_Y, _event_nr,
                     finde, lies_faehigkeiten, stabiler_pfad)

ABS_PRESSURE = 0x18
ABS_MT_POSITION_Y = 0x36
ABS_MT_TRACKING_ID = 0x39
ABS_MT_PRESSURE = 0x3A

ACHSEN = {
    ABS_X: "ABS_X", ABS_Y: "ABS_Y", ABS_PRESSURE: "ABS_PRESSURE",
    ABS_MT_SLOT: "ABS_MT_SLOT", ABS_MT_POSITION_X: "ABS_MT_POSITION_X",
    ABS_MT_POSITION_Y: "ABS_MT_POSITION_Y", ABS_MT_TRACKING_ID: "ABS_MT_TRACKING_ID",
    ABS_MT_PRESSURE: "ABS_MT_PRESSURE",
}

BUSSE = {0x01: "PCI", 0x03: "USB", 0x05: "Bluetooth", 0x06: "virtuell", 0x11: "PS/2",
         0x18: "I2C", 0x19: "Host", 0x1C: "SPI"}

ABSINFO = struct.Struct("6i")          # value, minimum, maximum, fuzz, flat, resolution
FELDER = ("wert", "min", "max", "fuzz", "flat", "aufloesung")


def eviocgabs(code):
    """_IOR('E', 0x40 + code, struct input_absinfo)."""
    return (2 << 30) | (ABSINFO.size << 16) | (ord("E") << 8) | (0x40 + code)


def lies_achsen(devpfad, codes):
    """{code: {wert, min, max, …}} per ioctl. Wirft OSError (z. B. PermissionError)."""
    import fcntl                                   # nur Linux
    fd = os.open(devpfad, os.O_RDONLY | os.O_NONBLOCK)
    try:
        ergebnis = {}
        for c in codes:
            puffer = fcntl.ioctl(fd, eviocgabs(c), bytes(ABSINFO.size))
            ergebnis[c] = dict(zip(FELDER, ABSINFO.unpack(puffer)))
        return ergebnis
    finally:
        os.close(fd)


def _lies(pfad, standard=""):
    try:
        return Path(pfad).read_text().strip()
    except (FileNotFoundError, NotADirectoryError, PermissionError):
        return standard


@dataclass
class Info:
    event: str
    name: str
    pfad: str = ""
    phys: str = ""
    uniq: str = ""
    bus: str = ""
    vendor: str = ""
    product: str = ""
    treiber: str = ""
    typ: str = ""                      # B, A, single
    direct: bool = False
    touchpad: bool = False
    provider: str = ""
    gewaehlt: bool = False             # würde setup.sh nehmen
    slots: int | None = None
    groesse_mm: tuple | None = None
    achsen: dict = field(default_factory=dict)       # Name → {min, max, …}
    hinweise: list = field(default_factory=list)

    def kivy_input(self):
        """Vorschlag für [input] touch = … aus den Rohbereichen."""
        x = self.achsen.get("ABS_MT_POSITION_X") or self.achsen.get("ABS_X")
        y = self.achsen.get("ABS_MT_POSITION_Y") or self.achsen.get("ABS_Y")
        if not (x and y):
            return None
        return (f"{self.provider},{self.pfad},min_position_x={x['min']},max_position_x={x['max']},"
                f"min_position_y={y['min']},max_position_y={y['max']}")


def sammle(root="/", achsen_leser=lies_achsen):
    """Alle Geräte mit Positionsachsen, in Event-Reihenfolge."""
    basis = Path(root) / "sys/class/input"
    gewaehlt = finde(root)
    infos = []
    for ev in sorted(basis.glob("event*"), key=lambda p: _event_nr(p.name)):
        try:
            f = lies_faehigkeiten(ev)
        except (FileNotFoundError, ValueError):
            continue
        if f.typ is None:
            continue
        dev = ev / "device"
        bus_nr = _lies(dev / "id/bustype", "0")
        info = Info(
            event=ev.name, name=_lies(dev / "name", ev.name),
            pfad=stabiler_pfad(ev.name, root)[0],
            phys=_lies(dev / "phys"), uniq=_lies(dev / "uniq"),
            bus=BUSSE.get(int(bus_nr, 16), f"0x{bus_nr}"),
            vendor=_lies(dev / "id/vendor"), product=_lies(dev / "id/product"),
            treiber=_treiber(dev),
            typ=f.typ, direct=f.direct, touchpad=f.touchpad,
            provider="mtdev" if f.typ == "A" else "hidinput",
            gewaehlt=gewaehlt is not None and gewaehlt.event == ev.name,
        )
        codes = sorted(c for c in ACHSEN if c in f.abs_bits)
        try:
            roh = achsen_leser(str(Path(root) / "dev/input" / ev.name), codes)
        except PermissionError:
            info.hinweise.append(f"keine Leserechte auf /dev/input/{ev.name} "
                                 "(Benutzer in Gruppe input?) – Achsen fehlen")
            roh = {}
        except OSError as e:
            info.hinweise.append(f"Achsen nicht lesbar: {e}")
            roh = {}
        info.achsen = {ACHSEN[c]: {k: v for k, v in w.items() if k != "wert"}
                       for c, w in roh.items()}
        _ableiten(info)
        infos.append(info)
    return infos


def _treiber(dev):
    """Treiber des Elterngeräts (z. B. hid-multitouch)."""
    for kandidat in (dev / "device/driver", dev / "driver"):
        if kandidat.is_symlink():
            return Path(os.readlink(kandidat)).name
    return ""


def _ableiten(info):
    slot = info.achsen.get("ABS_MT_SLOT")
    if slot:
        info.slots = slot["max"] + 1
    x = info.achsen.get("ABS_MT_POSITION_X") or info.achsen.get("ABS_X")
    y = info.achsen.get("ABS_MT_POSITION_Y") or info.achsen.get("ABS_Y")
    if x and y and x["aufloesung"] > 0 and y["aufloesung"] > 0:
        info.groesse_mm = (round((x["max"] - x["min"]) / x["aufloesung"], 1),
                           round((y["max"] - y["min"]) / y["aufloesung"], 1))


def als_text(infos):
    zeilen = []
    for i in infos:
        art = "Touchpad" if i.touchpad else ("Touchscreen" if i.direct else "ohne INPUT_PROP_DIRECT")
        kopf = f"{i.event}: {i.name}" + ("  ← von setup.sh gewählt" if i.gewaehlt else "")
        zeilen += [kopf, "-" * len(kopf)]
        for k, v in (("Pfad", i.pfad), ("Bus", i.bus), ("VID:PID", f"{i.vendor}:{i.product}"),
                     ("Treiber", i.treiber), ("phys", i.phys), ("uniq", i.uniq),
                     ("Art", art), ("Typ", i.typ), ("Provider", i.provider),
                     ("Slots", i.slots),
                     ("Größe", i.groesse_mm and f"{i.groesse_mm[0]} × {i.groesse_mm[1]} mm")):
            if v not in ("", None, ":"):
                zeilen.append(f"  {k:<9} {v}")
        if i.achsen:
            zeilen.append(f"  {'Achse':<20}{'min':>8}{'max':>8}{'fuzz':>6}{'flat':>6}{'res':>6}")
            for name, a in i.achsen.items():
                zeilen.append(f"  {name:<20}{a['min']:>8}{a['max']:>8}{a['fuzz']:>6}"
                              f"{a['flat']:>6}{a['aufloesung']:>6}")
        vorschlag = i.kivy_input()
        if vorschlag and not i.touchpad:
            zeilen.append(f"  Kivy:     touch = {vorschlag}")
        for h in i.hinweise:
            zeilen.append(f"  ! {h}")
        zeilen.append("")
    return "\n".join(zeilen)


def main(argv=None):
    p = argparse.ArgumentParser(prog="python3 -m inbetrieb.hwinfo")
    p.add_argument("--json", action="store_true", help="Ausgabe als JSON")
    p.add_argument("--root", default="/", help="Wurzel für sysfs/dev (Tests)")
    args = p.parse_args(argv)
    infos = sammle(args.root)
    if not infos:
        print("kein Gerät mit Positionsachsen gefunden", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps([asdict(i) | {"kivy_input": i.kivy_input()} for i in infos],
                         indent=2, ensure_ascii=False))
    else:
        print(als_text(infos), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())

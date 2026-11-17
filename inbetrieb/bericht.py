"""Touchtest-Bericht als JSON (D7)."""
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

RASTER = (16, 9)


def bericht_ordner():
    basis = os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state"
    return Path(basis) / "dyndesktop"


@dataclass
class Bericht:
    geraet: str = ""                                  # [input] touch aus config.ini
    fenster: tuple = (0, 0)                           # Breite, Höhe in Pixeln
    maximum: int = 0                                  # gleichzeitige Touches
    raster: tuple = RASTER
    heatmap: list = field(default_factory=lambda: [[0] * RASTER[0] for _ in range(RASTER[1])])
    geistertouches: list = field(default_factory=list)   # je Ruhephase: {dauer_s, anzahl, positionen}
    abweichungen: list = field(default_factory=list)     # {ziel, ist, px}
    doppelte_ereignisse: int = 0
    zeitpunkt: str = ""

    @property
    def abdeckung(self):
        """Anteil berührter Rasterfelder (0..1)."""
        felder = [z for zeile in self.heatmap for z in zeile]
        return sum(1 for z in felder if z) / len(felder)

    @property
    def max_abweichung(self):
        return max((a["px"] for a in self.abweichungen), default=None)

    def als_dict(self):
        d = asdict(self)
        d["abdeckung"] = round(self.abdeckung, 4)
        d["max_abweichung"] = self.max_abweichung
        d["geistertouches_gesamt"] = sum(g["anzahl"] for g in self.geistertouches)
        return d

    def speichern(self, ordner=None, jetzt=None):
        jetzt = jetzt or datetime.now()
        self.zeitpunkt = jetzt.isoformat(timespec="seconds")
        ordner = Path(ordner or bericht_ordner())
        ordner.mkdir(parents=True, exist_ok=True)
        pfad = ordner / f"touchtest-{jetzt:%Y%m%d-%H%M%S}.json"
        pfad.write_text(json.dumps(self.als_dict(), indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        return pfad

# dyndesktop

## Touch-Display mit Kivy kalibrieren

Kivy hat kein interaktives Kalibrier-Tool. Kalibriert wird auf einer von drei Ebenen – abhängig vom Input-Provider.

### 1. Provider-Parameter (`hidinput` / `mtdev`) – Rohwerte

Üblich auf Linux/Raspberry Pi, wenn Kivy direkt von `/dev/input/eventX` liest. In `~/.kivy/config.ini`:

```ini
[input]
touch = hidinput,/dev/input/event0,min_position_x=200,max_position_x=3900,min_position_y=250,max_position_y=3850,invert_y=1,rotation=90
```

Parameter:

- `min_position_x/y`, `max_position_x/y` – Rohbereich des Panels
- `invert_x`, `invert_y` – Achse spiegeln
- `rotation` – 0/90/180/270
- `min_pressure`, `max_pressure`

Rohwerte ermitteln: `evtest /dev/input/event0`, Ecken antippen, `ABS_X`/`ABS_Y` bzw. `ABS_MT_POSITION_X/Y` ablesen.

### 2. Postproc-Modul `calibration` – Feinkorrektur (normiert 0..1)

```ini
[postproc:calibration]
touch = xratio=0.98,yratio=1.02,xoffset=0.01,yoffset=-0.015
```

- Schlüssel = Gerätename aus `[input]` (hier `touch`)
- Formel: `sx = sx * xratio + xoffset`
- `auto=<Breite>x<Höhe>` für automatische Korrektur bei abweichender Display-/Touch-Auflösung

### 3. OS-Ebene

Nur relevant, wenn Kivy über SDL2/Window-Provider liest (nicht `hidinput`):

- libinput/Wayland: udev-Regel `ENV{LIBINPUT_CALIBRATION_MATRIX}="a b c d e f"`
- X11: `xinput_calibrator` bzw. `xinput set-prop … "Coordinate Transformation Matrix"`

**Wichtig:** Mit `hidinput`/`mtdev` liest Kivy evdev-Rohdaten – OS-Kalibrierung greift dann nicht, Kalibrierung muss in Kivy erfolgen.

### Prüfen

```bash
python -m kivy.tools.touchtracer   # oder: python app.py -m monitor
```

Touch-Punkte vs. Fingerposition vergleichen und Werte iterativ anpassen.

## Tisch-App (Prototyp)

Karten mit Text, Bild und Video auf einer Touch-Fläche (Paket `tisch/`).
`touch-demo/` bleibt als minimale Referenz unverändert.

### Start

```bash
poetry install
poetry run python -m tisch                       # Inhalte aus ./inhalte, im Fenster
poetry run python -m tisch --inhalte ~/karten    # anderer Inhaltsordner
KCFG_GRAPHICS_FULLSCREEN=auto poetry run python -m tisch   # Vollbild (Tisch)
poetry run pytest                                # Tests der Logik
```

Am Mac: Rechtsklick setzt einen zweiten „Finger“ (roter Punkt) zum Drehen und Skalieren.

### Kartentypen

| Endung | Karte |
|---|---|
| `.txt` | Text (UTF-8, umbrochen) |
| `.jpg`, `.jpeg`, `.png` | Bild im Seitenverhältnis |
| `.mp4`, `.webm` | Video, stumm, Endlosschleife (`ffpyplayer`) |

Je unterstützter Datei im Inhaltsordner entsteht eine Karte. Unterordner und andere
Endungen werden ignoriert. Unlesbare Dateien erscheinen als graue Fehlerkarte.

### Bearbeitung

- Karte 0,8 s mit einem Finger ruhig halten → Bearbeitung öffnet, virtuelle Tastatur erscheint neben der Karte.
- Textkarte: Text ändern, „Übernehmen“ schreibt die `.txt`-Datei.
- Bild-/Videokarte: anderen Dateinamen aus dem Inhaltsordner eingeben. Dateien werden nicht umbenannt.
- „Abbrechen“ oder ✕ auf der Tastatur verwirft. Es ist immer nur eine Bearbeitung offen.
- Tastatur am Rand (oben breiter Griff) ziehen, mit zwei Fingern am Rand drehen und skalieren.
- Eine physische Tastatur schreibt zusätzlich ins Eingabefeld.

Schwellen für den Langdruck: `tisch/langdruck.py` (`DAUER`, `SCHWELLE`).
Startgröße der Tastatur: `tisch/tastatur.py` (`STARTGROESSE`).

### Neuen Kartentyp hinzufügen

Eine Klasse von `Kartentyp` ableiten und einmal registrieren. Tischfläche, Gesten und
Bearbeitung bleiben unverändert.

```python
# tisch/typen/markdown.py
from pathlib import Path
from kivy.uix.label import Label
from .basis import Kartentyp

class MarkdownTyp(Kartentyp):
    name = "markdown"
    endungen = (".md",)

    def erzeuge_inhalt(self, pfad):          # Widget; Ausnahme → Fehlerkarte
        return Label(text=Path(pfad).read_text(encoding="utf-8"))

    # optional: groesse(inhalt), bearbeitungswert(pfad, inhalt),
    #           uebernehme(karte, wert) → wirft BearbeitungsFehler("Hinweis")
```

In `tisch/typen/__init__.py` unten ergänzen:

```python
from .markdown import MarkdownTyp
registriere(MarkdownTyp())
```

Eine bereits belegte Endung wird mit `ValueError` abgelehnt.

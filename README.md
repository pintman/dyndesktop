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

## Inbetriebnahme

Vom frischen Debian 13 bis zum kalibrierten Tisch (NUC oder Laptop, Beamer + IR-Rahmen).
Kompositor ist **niri**: Er begrenzt das App-Fenster per `struts` auf die Rahmenfläche,
der Rest des Beamerbilds bleibt schwarz.

### 1. System

1. Debian 13 netinst installieren, nur „SSH-Server“ und „Standard-Systemwerkzeuge“ wählen
   (kein Desktop). Benutzer mit `sudo`-Rechten anlegen.
2. Projekt holen und einrichten (als normaler Benutzer, **nicht** mit `sudo`):

   ```bash
   sudo apt install git
   git clone https://github.com/pintman/dyndesktop.git ~/proj/dyndesktop
   cd ~/proj/dyndesktop
   ./setup.sh
   ```

`setup.sh` lässt sich beliebig oft ausführen und meldet am Ende je Prüfpunkt OK/FEHLT
(Exit ≠ 0, wenn etwas fehlt). Es installiert Pakete, fügt den Benutzer zur Gruppe `input`
hinzu (danach neu anmelden), baut niri 26.04 nach `/usr/local/bin/niri` (nur beim ersten
Lauf, dauert), legt `.venv` an, erkennt den Rahmen über `/dev/input/by-id/` und schreibt
`~/.kivy/config.ini` sowie `~/.config/niri/config.kdl`. Ohne angeschlossenen Rahmen
meldet „Touch-Gerät“ FEHLT – Rahmen anstecken und erneut starten.

Hilfsbefehle (System-Python, auch ohne `.venv`):

```bash
python3 -m inbetrieb.geraet          # erkanntes Touch-Gerät, Typ A/B, Provider
python3 -m inbetrieb.kivyconfig zeigen
python3 -m inbetrieb.niriconfig struts
```

### 2. Testmodus (ohne Autostart)

Auf **tty1** (Tastatur am Rechner, nicht per SSH) anmelden und starten:

```bash
cd ~/proj/dyndesktop
DYNDESKTOP_START=inbetrieb niri
```

niri startet `kiosk.sh`, das einmalig `python -m inbetrieb` öffnet (Menü, maximiert in der
Rahmenfläche). „Beenden“ schließt auch niri. Notausgang: `Super+Shift+E`.

1. **Fläche**: Tab wählt die Kante, Pfeiltasten verschieben sie um 1 px (Umschalt: 10 px),
   Enter übernimmt, Esc stellt den Startzustand wieder her. Ziel: Fensterkanten liegen
   auf der Innenkante des Rahmens. Keystone vorher am Beamer einstellen.
2. **Kalibrieren**: 4 Kreuze nacheinander antippen, dann das Kontrollkreuz. Speichern
   schreibt `~/.kivy/config.ini` (Sicherung `config.ini.bak`) und öffnet den Touchtest.
3. **Touchtest**: gleichzeitige Touches (Maximum), Spuren, Heatmap, Ruhephase
   (Geistertouches), Ziele (Abweichung in px). Beim Verlassen entsteht ein Bericht
   `~/.local/state/dyndesktop/touchtest-<zeitstempel>.json`, abholbar per
   `scp <benutzer>@<rechner>:.local/state/dyndesktop/*.json .`

Notweg Fläche per SSH: in `~/.config/niri/config.kdl` den Block
`layout { struts { left …; right …; top …; bottom …; } }` ändern; niri lädt die Datei
sofort neu. `setup.sh` übernimmt die struts bei jedem Lauf.

Läuft Kivy nicht nativ unter Wayland, Fallback über Xwayland:
`DYNDESKTOP_X11=1 DYNDESKTOP_START=inbetrieb niri` (benötigt `xwayland-satellite`).

### 3. Kiosk

```bash
./setup.sh --kiosk && sudo reboot
```

Nach dem Booten startet `dyndesktop-kiosk.service` niri auf tty1, `kiosk.sh` startet
`python -m tisch` und nach einem Absturz nach 2 s neu. Strg+Alt+F2 wechselt auf eine
Textkonsole, SSH bleibt erreichbar. Logs: `journalctl -u dyndesktop-kiosk`.

Rückweg:

```bash
./setup.sh                       # Autostart aus (oder: sudo systemctl disable --now dyndesktop-kiosk)
cp ~/.kivy/config.ini.bak ~/.kivy/config.ini
cp ~/.config/niri/config.kdl.bak ~/.config/niri/config.kdl
```

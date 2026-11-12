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

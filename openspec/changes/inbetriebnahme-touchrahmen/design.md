# Design

## Context

- Bisher gibt es `touch-demo/app.py` (Kivy, Scatter-Karten) und Poetry zur Entwicklung am Mac. Die Kalibrier-Ebenen sind in `README.md` beschrieben.
- Zielrechner: Intel NUC oder Laptop mit Debian 13 ohne Desktop (Python 3.13). Kompositor ist cage.
- Rahmen: LMENGER LM-40IN. Laut Hersteller unter Linux eventuell nur Single-Touch, Multitouch-Protokoll Typ A oder B ist unbekannt.
- Getroffene Entscheidungen: Kivy (Variante C), Bash-Skript, Schalter `--kiosk`, ein Programm mit Menü. Siehe proposal.md.

## Goals / Non-Goals

**Goals:**
- In einem Durchgang vom frischen Debian bis „Rahmen geprüft und kalibriert“ – auch per Live-System auf dem Laptop während der Rückgabefrist.
- Reine Rechenlogik (Kalibrierung, Bearbeiten der Konfiguration, Geräteerkennung) ohne Kivy und ohne Hardware testbar.

**Non-Goals:**
- Installation des Betriebssystems selbst (Debian netinst bleibt Handarbeit).
- Kalibrierung auf OS-Ebene (libinput/udev), Chromium-Variante, Mehrmonitor-Betrieb über den Tisch-Bildschirm hinaus.
- Unterstützung anderer Distributionen als Debian 13.

## Decisions

### D1: Eingabeweg Kivy `hidinput`, Fallback `mtdev`
Kivy liest evdev direkt (`/dev/input/by-id/...-event-*`) und rechnet auf das eigene Fenster um.
- *Warum:* Auf dem Laptop entfällt die Zuordnung des Touch-Geräts zum Bildschirm, die cage nicht kann. Die Kalibrierung liegt vollständig in `~/.kivy/config.ini`.
- *Alternative:* SDL über libinput mit udev-`LIBINPUT_CALIBRATION_MATRIX`. Verworfen, weil cage kein map-to-output kennt und diese Kalibrierung nur außerhalb von Kivy greift.
- Typ-A-Geräte (keine `ABS_MT_SLOT`) bekommen `mtdev`.

### D2: Aufbau
```
setup.sh                     Bash, Ablauf + Bericht
inbetrieb/
  geraet.py                  nur Standardbibliothek: Touch-Gerät in /sys/class/input finden, Typ A/B
  kivyconfig.py              nur Standardbibliothek: config.ini gezielt ändern (configparser), Sicherung
  kalibrierung.py            reine Mathematik: Punkte -> rotation/invert + ratio/offset
  bericht.py                 Bericht-Datenklasse -> JSON
  app.py                     Kivy: Menü, Kalibrier-Screen, Touchtest-Screen
  __main__.py                Einstieg: python -m inbetrieb [--kalibrieren | --touchtest]
tests/                       pytest für geraet, kivyconfig, kalibrierung, bericht
```
- `setup.sh` ruft `geraet.py` und `kivyconfig.py` mit dem **System-Python** auf (`python3 -m inbetrieb.geraet`). Das klappt, bevor die venv existiert, und hält die Logik testbar statt in Bash.
- *Alternative:* alles in Bash (evtest-Ausgabe parsen, sed auf der INI). Verworfen: fehleranfällig, nicht testbar, und es würde die Kalibrierung überschreiben.

### D3: Geräteerkennung über sysfs
`/sys/class/input/event*/device/capabilities/abs` als Bitmaske: `ABS_MT_POSITION_X` (0x35) bedeutet Multitouch, `ABS_MT_SLOT` (0x2f) bedeutet Typ B. Daneben `INPUT_PROP_DIRECT` (Touchscreen statt Touchpad). Den stabilen Pfad liefert der passende Symlink in `/dev/input/by-id/`.
- *Warum:* Keine Root-Rechte und keine interaktiven Tools nötig. Mit Fixture-Verzeichnissen testbar.
- Mehrere Kandidaten → das erste Direct-Touch-Gerät nehmen und die übrigen im Bericht nennen.

### D4: Konfiguration gezielt ändern
`kivyconfig.py` liest `~/.kivy/config.ini` mit configparser und setzt nur:
- `[input]`: Schlüssel `touch = hidinput,<pfad>[,rotation=..,invert_x=..,invert_y=..]` und `mouse = mouse,disable_on_activity`
- `[postproc:calibration]`: `touch = xratio=..,yratio=..,xoffset=..,yoffset=..`

`setup.sh` übernimmt die Werte rotation/invert vom bestehenden `touch`-Eintrag, wenn es den Pfad neu schreibt. Vor jedem Schreiben entsteht `config.ini.bak`. Kommentare in der INI gehen verloren, das ist in Kauf genommen (Kivy schreibt die Datei ohnehin selbst neu).

### D5: Rohmodus beim Kalibrieren
Die Kalibrierpunkte müssen ohne alte Korrektur erfasst werden (Spec touch-kalibrierung). `python -m inbetrieb --kalibrieren` entfernt dazu **im Speicher** (`kivy.config.Config`, vor dem Import von `kivy.core`/Window) den Abschnitt `[postproc:calibration]` sowie rotation/invert aus `[input] touch`. Es schreibt nichts in die Datei.
- Menü → Kalibrieren startet sich daher per `os.execv` mit `--kalibrieren` neu. Speichern → `os.execv` mit `--touchtest`, jetzt mit den gespeicherten Werten.
- `execv` behält die PID. cage sieht keinen Prozess enden und bleibt deshalb aktiv.

### D6: Kalibrier-Mathematik
Eingabe: 4 Paare (Soll normiert, Ist normiert) im Rohmodus.
1. Ausrichtung: Für jede der 8 Kombinationen aus rotation ∈ {0,90,180,270} und invert ∈ {0,1}² wird Ist so transformiert, wie Kivy es tut. Gewählt wird die Kombination mit dem kleinsten Fehler nach linearer Anpassung. Gleichwertige Kombinationen werden auf die kanonische Form ohne Spiegelung reduziert.
2. Je Achse lineare Regression `soll = ist * ratio + offset` (Kivy-Formel `sx = sx * xratio + xoffset`).
3. Kontrolle: das 5. Kreuz mit vorläufig angewendeter Korrektur (im Programm selbst, nicht über Kivy-postproc). Die Schwelle für „große Abweichung“ ist 2 % der Bilddiagonale.

Die Reihenfolge der Kivy-Transformationen (Normierung → invert → rotation → postproc) ist eine Annahme. Ein Test bildet sie gegen den Kivy-Quelltext nach (siehe Risiken).

### D7: Touchtest
- Markierung + Spur pro `touch.uid` in einer Farbe aus einer festen Palette. Anzahl/Maximum über die Menge aktiver uids.
- Heatmap-Raster 16×9 passend zu 16:9, gezählt über `touch_down`/`touch_move`.
- Ruhephase: Knopf mit wählbarer Dauer (10/30/60 s). Jedes `touch_down` in dieser Zeit zählt als Geistertouch.
- Doppelte Ereignisse: Ein `touch` mit `device == "mouse"` innerhalb von 100 ms nach einem echten Touch gilt als Duplikat.
- Bericht: `~/.local/state/dyndesktop/touchtest-YYYYmmdd-HHMMSS.json`, Pfad wird angezeigt.

### D8: Kiosk über systemd-System-Unit
`/etc/systemd/system/dyndesktop-kiosk.service` mit `User=<benutzer>`, `PAMName=login`, `TTYPath=/dev/tty1`, `WorkingDirectory=<projekt>`, `ExecStart=/usr/bin/cage -s -m last -- <projekt>/.venv/bin/python -m tisch`, `Restart=always`, `Conflicts=getty@tty1.service`. So empfiehlt es auch die cage-Doku.
- Ohne `--kiosk`: Die Unit wird bei Bedarf abgelegt, aber deaktiviert (`systemctl disable`).
- *Alternative:* greetd oder Getty-Autologin + `.bash_profile`. Verworfen: mehr bewegliche Teile.
- Vollbild für die Tisch-App (`python -m tisch`, Change `prototyp-kartentisch`) über Kivys Env-Override `Environment=KCFG_GRAPHICS_FULLSCREEN=auto` in der Unit. So bleibt die App unverändert und läuft am Mac weiter im Fenster.

### D9: Laptop
`cage -m last` zeigt die App auf dem zuletzt erkannten Ausgang (dem HDMI-Fernseher). `inbetrieb` setzt immer `Window.fullscreen = "auto"`. Weil hidinput sich auf das Fenster bezieht, braucht es keine weitere Zuordnung.

### D10: Python-Umgebung
`setup.sh` legt `.venv` im Projektverzeichnis an (`python3 -m venv`) – ohne Poetry auf dem Tisch. Die Abhängigkeiten liest es mit `tomllib` (System-Python 3.13) aus `[project].dependencies` in `pyproject.toml` und installiert sie per `.venv/bin/pip install` (derzeit `kivy>=2.3`, `ffpyplayer`). `pip install .` scheidet aus, weil `package-mode = false` gesetzt ist. Poetry bleibt für die Entwicklung, pytest ist bereits Dev-Gruppe.

## Risks / Trade-offs

- [Rahmen meldet unter Linux nur Single-Touch] → `setup.sh` warnt sofort, der Touchtest zeigt Maximum 1. Das reicht als Beleg für die Rückgabe.
- [Kivy-Wheel bringt SDL2 ohne Wayland-Unterstützung mit] → Paket `xwayland` installieren, damit cage X11-Clients zeigt. Bei der ersten Inbetriebnahme prüfen. Der Touch ist davon unabhängig, weil hidinput evdev direkt liest.
- [Kivy-Transformationsreihenfolge/Default `invert_y` anders als angenommen] → ein Test prüft `kalibrierung.py` gegen die Kivy-Implementierung (`kivy/input/providers/hidinput.py`, `postproc/calibration.py`) mit konstruierten Punkten. Abschließend prüft das Kontrollkreuz am echten Gerät.
- [`/dev/input/by-id` fehlt bei manchen Geräten] → Fallback auf `/dev/input/by-path`, sonst `eventX` mit Warnung.
- [configparser entfernt Kommentare in config.ini] → hingenommen, Sicherung `.bak` vorhanden.
- [Kiosk sperrt aus, wenn die App sofort abstürzt] → `-s` für den Wechsel auf die Textkonsole, SSH bleibt erreichbar, `Restart=always` mit `RestartSec=2`.
- [Gruppe `input` erst nach Neuanmeldung wirksam] → `setup.sh` meldet das. Der Geräte-Prüfpunkt liest sysfs und braucht dafür keine Gruppenrechte.

## Migration Plan

Neue Dateien, keine Migration. Rückweg: `sudo systemctl disable --now dyndesktop-kiosk`, `config.ini.bak` zurückkopieren.

## Open Questions

- Ob `-m last` an jedem Laptop den Fernseher trifft, zeigt sich erst am Gerät. Notfalls bekommt die Unit eine Option für einen festen Ausgang.

# Design

## Context

- Bisher gibt es `touch-demo/app.py` (Kivy, Scatter-Karten) und Poetry zur Entwicklung am Mac. Die Kalibrier-Ebenen sind in `README.md` beschrieben.
- Zielrechner: Intel NUC oder Laptop mit Debian 13 ohne Desktop (Python 3.13). Kompositor ist niri.
- Aufbau: Der Rahmen liegt auf einem Tisch, ein fest montierter Beamer projiziert von oben. Das Beamerbild ist größer als der Rahmen und lässt sich nicht auf ihn einstellen.
- Rahmen: LMENGER LM-40IN. Laut Hersteller unter Linux eventuell nur Single-Touch, Multitouch-Protokoll Typ A oder B ist unbekannt.
- Getroffene Entscheidungen: Kivy (Variante C), Bash-Skript, Schalter `--kiosk`, ein Programm mit Menü, niri statt cage. Siehe proposal.md.

## Goals / Non-Goals

**Goals:**
- In einem Durchgang vom frischen Debian bis „Rahmen geprüft und kalibriert“ – auch per Live-System auf dem Laptop während der Rückgabefrist.
- Apps nutzen nur die Rahmenfläche, ohne dass `tisch/` oder die Kalibrier-Mathematik eine Teilfläche kennen müssen.
- Reine Rechenlogik (Kalibrierung, Bearbeiten der Konfigurationen, Geräte- und Ausgangserkennung) ohne Kivy und ohne Hardware testbar.

**Non-Goals:**
- Installation des Betriebssystems selbst (Debian netinst bleibt Handarbeit).
- Kalibrierung auf OS-Ebene (libinput/udev), Chromium-Variante, Mehrmonitor-Betrieb über den Tisch-Bildschirm hinaus.
- Trapezkorrektur in Software. Die übernimmt der Beamer (Keystone).
- Unterstützung anderer Distributionen als Debian 13.

## Decisions

### D1: Eingabeweg Kivy `hidinput`, Fallback `mtdev`
Kivy liest evdev direkt (`/dev/input/by-id/...-event-*`) und rechnet auf das eigene Fenster um.
- *Warum:* Liegt das Fenster per niri genau auf dem Rahmen (D12), bildet der Rahmen bereits ohne Korrektur annähernd auf das Fenster ab. Die Feinkalibrierung liegt vollständig in `~/.kivy/config.ini`.
- niri selbst bekommt den Touch nicht (`input { touch { off } }`). So gibt es keine doppelten Ereignisse über SDL und keine Kompositor-Gesten.
- *Alternative:* SDL über libinput mit `map-to-output` und udev-`LIBINPUT_CALIBRATION_MATRIX`. Verworfen: `map-to-output` bezieht sich auf den ganzen Ausgang, nicht auf die Rahmenfläche, und die Kalibrierung griffe nur außerhalb von Kivy.
- Typ-A-Geräte (keine `ABS_MT_SLOT`) bekommen `mtdev`.

### D2: Aufbau
```
setup.sh                     Bash, Ablauf + Bericht
kiosk.sh                     Startskript unter niri (Schleife im Kiosk, einmalig im Testmodus)
inbetrieb/
  geraet.py                  nur Standardbibliothek: Touch-Gerät in /sys/class/input finden, Typ A/B
  kivyconfig.py              nur Standardbibliothek: config.ini gezielt ändern (configparser), Sicherung
  niriconfig.py              nur Standardbibliothek: config.kdl erzeugen, struts lesen/schreiben, interne Ausgänge finden
  kalibrierung.py            reine Mathematik: Punkte -> rotation/invert + ratio/offset
  bericht.py                 Bericht-Datenklasse -> JSON
  app.py                     Kivy: Menü, Flächen-Screen, Kalibrier-Screen, Touchtest-Screen
  __main__.py                Einstieg: python -m inbetrieb [--flaeche | --kalibrieren | --touchtest]
tests/                       pytest für geraet, kivyconfig, niriconfig, kalibrierung, bericht
```
- `setup.sh` ruft `geraet.py`, `kivyconfig.py` und `niriconfig.py` mit dem **System-Python** auf (`python3 -m inbetrieb.geraet`). Das klappt, bevor die venv existiert, und hält die Logik testbar statt in Bash.
- *Alternative:* alles in Bash (evtest-Ausgabe parsen, sed auf INI/KDL). Verworfen: fehleranfällig, nicht testbar, und es würde Kalibrierung und struts überschreiben.

### D3: Geräteerkennung über sysfs
`/sys/class/input/event*/device/capabilities/abs` als Bitmaske: `ABS_MT_POSITION_X` (0x35) bedeutet Multitouch, `ABS_MT_SLOT` (0x2f) bedeutet Typ B. Daneben `INPUT_PROP_DIRECT` (Touchscreen statt Touchpad). Den stabilen Pfad liefert der passende Symlink in `/dev/input/by-id/`.
- *Warum:* Keine Root-Rechte und keine interaktiven Tools nötig. Mit Fixture-Verzeichnissen testbar.
- Mehrere Kandidaten → das erste Direct-Touch-Gerät nehmen und die übrigen im Bericht nennen.

### D4: Kivy-Konfiguration gezielt ändern
`kivyconfig.py` liest `~/.kivy/config.ini` mit configparser und setzt nur:
- `[input]`: Schlüssel `touch = hidinput,<pfad>[,rotation=..,invert_x=..,invert_y=..]` und `mouse = mouse,disable_on_activity`
- `[postproc:calibration]`: `touch = xratio=..,yratio=..,xoffset=..,yoffset=..`

`setup.sh` übernimmt die Werte rotation/invert vom bestehenden `touch`-Eintrag, wenn es den Pfad neu schreibt. Vor jedem Schreiben entsteht `config.ini.bak`. Kommentare in der INI gehen verloren, das ist in Kauf genommen (Kivy schreibt die Datei ohnehin selbst neu).

### D5: Rohmodus beim Kalibrieren
Die Kalibrierpunkte müssen ohne alte Korrektur erfasst werden (Spec touch-kalibrierung). `python -m inbetrieb --kalibrieren` entfernt dazu **im Speicher** (`kivy.config.Config`, vor dem Import von `kivy.core`/Window) den Abschnitt `[postproc:calibration]` sowie rotation/invert aus `[input] touch`. Es schreibt nichts in die Datei.
- Menü → Kalibrieren startet sich daher per `os.execv` mit `--kalibrieren` neu. Speichern → `os.execv` mit `--touchtest`, jetzt mit den gespeicherten Werten.
- `execv` behält die PID. `kiosk.sh` sieht keinen Prozess enden und startet nichts doppelt. niri öffnet das neue Fenster wieder maximiert.

### D6: Kalibrier-Mathematik
Eingabe: 4 Paare (Soll normiert, Ist normiert) im Rohmodus.
1. Ausrichtung: Für jede der 8 Kombinationen aus rotation ∈ {0,90,180,270} und invert ∈ {0,1}² wird Ist so transformiert, wie Kivy es tut. Gewählt wird die Kombination mit dem kleinsten Fehler nach linearer Anpassung. Gleichwertige Kombinationen werden auf die kanonische Form ohne Spiegelung reduziert.
2. Je Achse lineare Regression `soll = ist * ratio + offset` (Kivy-Formel `sx = sx * xratio + xoffset`).
3. Kontrolle: das 5. Kreuz mit vorläufig angewendeter Korrektur (im Programm selbst, nicht über Kivy-postproc). Die Schwelle für „große Abweichung“ ist 2 % der Fensterdiagonale.

Weil das Fenster per niri auf der Rahmenfläche liegt, liegen die Kreuze nahe den Fensterecken auch auf dem Rahmen. Bleibt nach dem Einstellen der Fläche ein Restüberstand, ergibt die Regression `ratio` etwas größer oder kleiner als 1.

Die Reihenfolge der Kivy-Transformationen (Normierung → invert → rotation → postproc) ist eine Annahme. Ein Test bildet sie gegen den Kivy-Quelltext nach (siehe Risiken).

### D7: Touchtest
- Markierung + Spur pro `touch.uid` in einer Farbe aus einer festen Palette. Anzahl/Maximum über die Menge aktiver uids.
- Heatmap-Raster 16×9 über das Fenster (= Rahmenfläche), gezählt über `touch_down`/`touch_move`.
- Ruhephase: Knopf mit wählbarer Dauer (10/30/60 s). Jedes `touch_down` in dieser Zeit zählt als Geistertouch. Gemessen wird bei laufendem Beamer, weil dessen IR-Anteil Störquelle sein kann.
- Doppelte Ereignisse: Ein `touch` mit `device == "mouse"` innerhalb von 100 ms nach einem echten Touch gilt als Duplikat.
- Bericht: `~/.local/state/dyndesktop/touchtest-YYYYmmdd-HHMMSS.json`, Pfad wird angezeigt.

### D8: Kiosk über systemd-System-Unit
`/etc/systemd/system/dyndesktop-kiosk.service` mit `User=<benutzer>`, `PAMName=login`, `TTYPath=/dev/tty1`, `WorkingDirectory=<projekt>`, `Environment=DYNDESKTOP_KIOSK=1`, `ExecStart=<niri>`, `Restart=always`, `RestartSec=2`, `Conflicts=getty@tty1.service`.
- niri startet über `spawn-at-startup` das Skript `<projekt>/kiosk.sh`. Mit `DYNDESKTOP_KIOSK=1` startet es `python -m tisch` in einer Endlosschleife (2 s Pause), sodass ein Absturz der App einen Neustart auslöst. niri selbst endet nicht, wenn die App endet.
- Testmodus ohne Unit: auf tty1 anmelden und `DYNDESKTOP_START=inbetrieb niri` aufrufen. `kiosk.sh` startet dann einmalig `python -m inbetrieb`. Menü → Beenden schließt die App und beendet niri über `niri msg action quit --skip-confirmation`.
- Ohne `--kiosk`: Die Unit wird bei Bedarf abgelegt, aber deaktiviert (`systemctl disable`).
- Kein Vollbild: Die Apps laufen maximiert in der Rahmenfläche (D12). `KCFG_GRAPHICS_FULLSCREEN` wird nicht gesetzt, weil Vollbild die struts ignoriert.
- *Alternative:* greetd oder Getty-Autologin + `.bash_profile`. Verworfen: mehr bewegliche Teile.

### D9: Laptop
`niriconfig.py` ermittelt interne Anzeigen über `/sys/class/drm/card*-{eDP,LVDS,DSI}-*` und schreibt für jede `output "<name>" { off; }`. Die App erscheint damit auf dem einzigen aktiven Ausgang (Beamer). Weil hidinput sich auf das Fenster bezieht, braucht der Touch keine weitere Zuordnung.

### D10: Python-Umgebung
`setup.sh` legt `.venv` im Projektverzeichnis an (`python3 -m venv`) – ohne Poetry auf dem Tisch. Die Abhängigkeiten liest es mit `tomllib` (System-Python 3.13) aus `[project].dependencies` in `pyproject.toml` und installiert sie per `.venv/bin/pip install` (derzeit `kivy>=2.3`, `ffpyplayer`). `pip install .` scheidet aus, weil `package-mode = false` gesetzt ist. Poetry bleibt für die Entwicklung, pytest ist bereits Dev-Gruppe.

### D11: niri installieren
niri ist nicht als Debian-13-Paket verfügbar. `setup.sh` nutzt das apt-Paket, falls es eines gibt, und baut sonst eine **feste Version** (Variable `NIRI_VERSION`, Git-Tag) mit `cargo install --locked --git … --tag …` nach `/usr/local/bin/niri`.
- Build-Abhängigkeiten kommen per apt (u. a. clang, libudev, libgbm, libxkbcommon, libwayland, libinput, libseat, libpipewire, libpango, libdisplay-info, libdbus, libsystemd). Ist Debians `rustc` älter als die MSRV der gewählten niri-Version, installiert das Skript Rust per rustup für den Benutzer.
- Wiederholbarkeit: Gebaut wird nur, wenn `niri --version` nicht zu `NIRI_VERSION` passt.
- Xwayland: Die App soll nativ unter Wayland laufen (`SDL_VIDEODRIVER=wayland` in `kiosk.sh`). Klappt das mit dem SDL2 aus dem Kivy-Wheel nicht, baut das Skript zusätzlich `xwayland-satellite`, das niri automatisch startet.
- *Alternative:* cage mit eigener Teilflächen-Logik in `tisch/` und `inbetrieb/`. Verworfen: cage kann Fenster nicht auf einen Teil des Ausgangs begrenzen, jede App müsste die Rahmenfläche selbst kennen.

### D12: niri-Konfiguration und Rahmenfläche
`niriconfig.py` erzeugt `~/.config/niri/config.kdl` vollständig aus einer Vorlage. Die Datei gehört dem Skript, vor jedem Schreiben entsteht `config.kdl.bak`. Inhalt:
- `layout { gaps 0; struts { left L; right R; top T; bottom B; }; focus-ring { off; }; border { off; }; }`, schwarzer Hintergrund
- `window-rule { open-maximized true; }`, `prefer-no-csd`
- `input { touch { off; } }` (D1), Cursor nach kurzer Inaktivität ausblenden, Hotkey-Übersicht beim Start aus
- interne Ausgänge aus (D9), `spawn-at-startup "<projekt>/kiosk.sh"`

Die struts (logische Pixel) sind die Rahmenfläche. Beim Neuschreiben übernimmt `niriconfig.py` die struts aus der bestehenden Datei, ohne Datei sind alle 0. niri lädt die Datei bei Änderung selbst neu, das Fenster folgt sofort.
- Annahme: Der Ausgang läuft mit `scale 1`, damit struts Pixeln des Beamerbilds entsprechen. Die Vorlage setzt das für den aktiven Ausgang.

### D13: Fläche einstellen
`python -m inbetrieb --flaeche` zeigt einen hellen Rand an den Fensterkanten. Bedient wird per Tastatur, weil der Touch vor dem Einstellen nicht zum Bild passt:
- Tab wählt die Kante, Pfeiltasten verschieben sie um 1 px (mit Umschalt 10 px). Jede Änderung schreibt die struts über `niriconfig.py`. niri lädt neu, das Fenster wandert, der Rand bleibt an den Fensterkanten.
- Enter übernimmt und kehrt ins Menü zurück, Esc stellt die struts vom Start des Modus wieder her.
- Nach einer Änderung weist das Menü darauf hin, dass neu kalibriert werden sollte.
- *Alternative:* struts per SSH in `config.kdl` von Hand ändern. Bleibt als Notweg möglich und ist im README beschrieben.

## Risks / Trade-offs

- [Rahmen meldet unter Linux nur Single-Touch] → `setup.sh` warnt sofort, der Touchtest zeigt Maximum 1. Das reicht als Beleg für die Rückgabe.
- [niri-Build scheitert oder dauert lange (Rust, viele Abhängigkeiten)] → feste Version, Build nur einmal. Bei der ersten Inbetriebnahme auf dem Laptop prüfen, notfalls Rückfall auf cage mit Teilfläche in der App (eigener Change).
- [SDL2 aus dem Kivy-Wheel ohne Wayland-Unterstützung] → `xwayland-satellite` als Fallback (D11). Der Touch ist davon unabhängig, weil hidinput evdev direkt liest.
- [`touch { off }` oder `open-maximized` in der gewählten niri-Version anders benannt] → beim Festlegen von `NIRI_VERSION` gegen deren Doku prüfen. Ein Test vergleicht die erzeugte Datei mit `niri validate`, sofern niri installiert ist.
- [Trapezverzerrung durch schräge Projektion] → Keystone am Beamer. Die Kalibrierung korrigiert nur linear je Achse, eine Restverzerrung zeigt die Genauigkeitsprüfung.
- [Beamer-IR löst Geistertouches aus, Hände werfen Schatten] → Ruhephase bei laufendem Beamer messen. Schatten sind ein Aufbauthema, kein Software-Thema.
- [Kivy-Transformationsreihenfolge/Default `invert_y` anders als angenommen] → ein Test prüft `kalibrierung.py` gegen die Kivy-Implementierung (`kivy/input/providers/hidinput.py`, `postproc/calibration.py`) mit konstruierten Punkten. Abschließend prüft das Kontrollkreuz am echten Gerät.
- [`/dev/input/by-id` fehlt bei manchen Geräten] → Fallback auf `/dev/input/by-path`, sonst `eventX` mit Warnung.
- [configparser entfernt Kommentare in config.ini, eigene Änderungen an config.kdl gehen verloren] → hingenommen, Sicherungen `.bak` vorhanden.
- [Kiosk sperrt aus, wenn die App sofort abstürzt] → niri bleibt laufen, `kiosk.sh` startet mit Pause neu. Strg+Alt+F2 erreicht die Textkonsole, SSH bleibt erreichbar.
- [Gruppe `input` erst nach Neuanmeldung wirksam] → `setup.sh` meldet das. Der Geräte-Prüfpunkt liest sysfs und braucht dafür keine Gruppenrechte.

## Migration Plan

Neue Dateien, keine Migration. Rückweg: `sudo systemctl disable --now dyndesktop-kiosk`, `config.ini.bak` und `config.kdl.bak` zurückkopieren.

## Open Questions

- Welche niri-Version als `NIRI_VERSION` (MSRV gegen Debian-`rustc`, Optionsnamen) – beim Umsetzen von Task 7.2 festlegen.
- Ob das Kivy-Wheel nativ unter Wayland läuft – zeigt sich beim ersten Start auf dem Laptop.

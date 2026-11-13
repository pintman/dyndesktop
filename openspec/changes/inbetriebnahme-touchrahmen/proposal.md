# Proposal

## Why

Der IR-Touchrahmen (LMENGER LM-40IN) soll an einem Intel NUC oder Laptop unter Linux laufen. Bisher gibt es dafür nur Notizen (`plan-touch-display.md`, `README.md`) und die Demo `touch-demo/app.py`. Es fehlt ein wiederholbarer Weg von einem frischen Debian bis zum laufenden Tisch. Außerdem fehlt ein Werkzeug, mit dem man Multitouch-Fähigkeit und Kalibrierung prüft – schnell, solange die Rückgabefrist läuft.

Der Rahmen liegt auf einem Tisch, auf den ein fest montierter Beamer projiziert. Das Beamerbild ist größer als der Rahmen. Die Apps dürfen deshalb nur den Teil des Bildes nutzen, den der Rahmen abdeckt (Rahmenfläche).

## What Changes

- Neues Bash-Skript `setup.sh`: richtet ein frisches Debian 13 (ohne Desktop) für den Tisch ein. Es lässt sich mehrfach ausführen und meldet am Ende pro Prüfpunkt OK/FEHLT. Dazu gehören Pakete (evtest, libinput-tools, python3-venv), der Kompositor niri, die Gruppe `input`, venv mit Kivy, das Touch-Gerät über `/dev/input/by-id`, die Kivy-Eingabekonfiguration und die niri-Konfiguration.
- Kompositor **niri** statt cage: Über `struts` begrenzt niri die Fensterfläche auf die Rahmenfläche, die Apps laufen maximiert statt im Vollbild. Tisch-App und Kalibrierung brauchen dadurch keine eigene Teilflächen-Logik. niri ist nicht als Debian-13-Paket verfügbar und wird bei Bedarf in einer festen Version gebaut.
- Schalter `setup.sh --kiosk`: richtet zusätzlich den Autostart ein (systemd-Unit → niri → `python -m tisch`). Ohne den Schalter bleibt der Autostart aus (Testmodus per SSH).
- Neues Kivy-Programm `inbetrieb` (Start: `python -m inbetrieb`) mit Menü:
  - **Fläche**: verschiebt die Ränder der Fensterfläche per Pfeiltasten, bis das Fenster genau auf dem Rahmen liegt, und speichert sie als struts in der niri-Konfiguration.
  - **Kalibrieren**: 4 Fadenkreuze plus 1 Kontrollkreuz. Das Programm ermittelt Drehung/Spiegelung und Skalierung/Versatz und speichert das Ergebnis in `~/.kivy/config.ini`. Danach startet es neu und öffnet den Touchtest.
  - **Touchtest**: Anzahl gleichzeitiger Touches, Touch-IDs mit Spuren, Heatmap, Geistertouches in einer Ruhephase, Restabweichung an Zielpunkten. Der Bericht erscheint auf dem Bildschirm und wird als JSON-Datei gespeichert.
- Touch-Eingabe über Kivy `hidinput` (Fallback `mtdev` bei Typ-A-Geräten). Kalibriert wird nur in Kivy, nicht auf OS-Ebene.
- README um einen Abschnitt zur Inbetriebnahme ergänzt.

## Capabilities

### New Capabilities

- `tisch-einrichtung`: Einrichtung eines Debian-Rechners als Touch-Tisch per Skript, inklusive Kompositor niri, Erkennung des Touch-Geräts, Kivy-Eingabekonfiguration und optionalem Kiosk-Autostart.
- `touch-kalibrierung`: Interaktive Anpassung der Fensterfläche an den Rahmen und Kalibrierung des Touchrahmens gegenüber dem Bild, mit dauerhafter Speicherung der Werte.
- `touch-diagnose`: Interaktiver Touchtest, der Multitouch-Fähigkeit, Abdeckung, Geistertouches und Genauigkeit misst und als Bericht ausgibt.

### Modified Capabilities

Keine.

## Impact

- Neue Dateien: `setup.sh`, `kiosk.sh` (Startskript unter niri), ein neues Python-Paket `inbetrieb/` (Menü, Fläche, Kalibrierung, Touchtest, Bearbeiten der Konfigurationen), Tests dazu.
- `pyproject.toml`: pytest als Entwicklungsabhängigkeit.
- Zielsystem: Debian 13. Das Skript schreibt in `/etc/systemd/system/` (nur mit `--kiosk`), nach `/usr/local/bin/` (niri, falls gebaut), in die Gruppenzugehörigkeit des Benutzers, nach `~/.kivy/config.ini` und nach `~/.config/niri/config.kdl`.
- `touch-demo/app.py` bleibt unverändert. Im Kiosk-Modus startet die Tisch-App `python -m tisch` (Change `prototyp-kartentisch`) maximiert in der Rahmenfläche. Der Code von `tisch/` bleibt unverändert, weil er sich nach `Window.size` richtet.
- Nicht betroffen: Variante B (Chromium). Eine Kalibrierung auf OS-Ebene wäre dafür später nötig.

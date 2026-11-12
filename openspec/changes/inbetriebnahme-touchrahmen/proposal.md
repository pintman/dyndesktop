# Proposal

## Why

Der IR-Touchrahmen (LMENGER LM-40IN) soll an einem Intel NUC oder Laptop unter Linux laufen. Bisher gibt es dafür nur Notizen (`plan-touch-display.md`, `README.md`) und die Demo `touch-demo/app.py`. Es fehlt ein wiederholbarer Weg von einem frischen Debian bis zum laufenden Tisch. Außerdem fehlt ein Werkzeug, mit dem man Multitouch-Fähigkeit und Kalibrierung prüft – schnell, solange die Rückgabefrist läuft.

## What Changes

- Neues Bash-Skript `setup.sh`: richtet ein frisches Debian 13 (ohne Desktop) für den Tisch ein. Es lässt sich mehrfach ausführen und meldet am Ende pro Prüfpunkt OK/FEHLT. Dazu gehören Pakete (cage, evtest, libinput-tools, python3-venv), die Gruppe `input`, venv mit Kivy, das Touch-Gerät über `/dev/input/by-id` und die Kivy-Eingabekonfiguration.
- Schalter `setup.sh --kiosk`: richtet zusätzlich den Autostart ein (systemd-Unit → cage → `app.py`). Ohne den Schalter bleibt der Autostart aus (Testmodus per SSH).
- Neues Kivy-Programm `inbetrieb` (Start: `python -m inbetrieb`) mit Menü:
  - **Kalibrieren**: 4 Fadenkreuze plus 1 Kontrollkreuz. Das Programm ermittelt Drehung/Spiegelung und Skalierung/Versatz und speichert das Ergebnis in `~/.kivy/config.ini`. Danach startet es neu und öffnet den Touchtest.
  - **Touchtest**: Anzahl gleichzeitiger Touches, Touch-IDs mit Spuren, Heatmap, Geistertouches in einer Ruhephase, Restabweichung an Zielpunkten. Der Bericht erscheint auf dem Bildschirm und wird als JSON-Datei gespeichert.
- Touch-Eingabe über Kivy `hidinput` (Fallback `mtdev` bei Typ-A-Geräten). Kalibriert wird nur in Kivy, nicht auf OS-Ebene.
- README um einen Abschnitt zur Inbetriebnahme ergänzt.

## Capabilities

### New Capabilities

- `tisch-einrichtung`: Einrichtung eines Debian-Rechners als Touch-Tisch per Skript, inklusive Erkennung des Touch-Geräts, Kivy-Eingabekonfiguration und optionalem Kiosk-Autostart.
- `touch-kalibrierung`: Interaktive Kalibrierung des Touchrahmens gegenüber dem Bild und dauerhafte Speicherung der Werte.
- `touch-diagnose`: Interaktiver Touchtest, der Multitouch-Fähigkeit, Abdeckung, Geistertouches und Genauigkeit misst und als Bericht ausgibt.

### Modified Capabilities

Keine.

## Impact

- Neue Dateien: `setup.sh`, ein neues Python-Paket `inbetrieb/` (Menü, Kalibrierung, Touchtest, Bearbeiten der Konfiguration), Tests dazu.
- `pyproject.toml`: pytest als Entwicklungsabhängigkeit.
- Zielsystem: Debian 13. Das Skript schreibt in `/etc/systemd/system/` (nur mit `--kiosk`), in die Gruppenzugehörigkeit des Benutzers und nach `~/.kivy/config.ini`.
- `touch-demo/app.py` bleibt unverändert und ist im Kiosk-Modus die gestartete App.
- Nicht betroffen: Variante B (Chromium). Eine Kalibrierung auf OS-Ebene wäre dafür später nötig.

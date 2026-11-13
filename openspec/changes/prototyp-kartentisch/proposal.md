# Proposal

## Why

`touch-demo/app.py` zeigt nur, dass Kivy-Scatter-Karten mit Schwung auf dem Tisch funktionieren. Für den eigentlichen Tisch fehlt ein erster Prototyp mit verschiedenen Inhalten (Text, Bild, Video), Bearbeitung per Touch und einer Struktur, in die sich weitere Kartentypen einhängen lassen. Er soll auf dem Rechner laufen, den der Change `inbetriebnahme-touchrahmen` einrichtet.

## What Changes

- Neues Python-Paket `tisch/` (Start: `python -m tisch [--inhalte <ordner>]`). Ausgangspunkt ist die Logik aus `touch-demo/app.py`. `touch-demo/` selbst bleibt unverändert.
- Karten werden aus einem Inhaltsordner geladen: `.txt` → Textkarte, Bilddateien → Bildkarte, Videodateien → Videokarte.
- Jede Karte lässt sich per Multitouch verschieben, drehen und skalieren. Nach dem Loslassen rutscht sie mit Reibung weiter (Physikmodell aus `touch-demo`).
- Kartentypen hängen an einer Registry. Ein neuer Typ braucht nur eine neue Klasse und eine Registrierung, keine Änderung am Tisch.
- Langer Touch auf eine Karte öffnet die Bearbeitung mit einer virtuellen Tastatur:
  - Textkarte: Inhalt ändern. Beim Übernehmen wird die `.txt`-Datei zurückgeschrieben.
  - Bild-/Videokarte: Dateinamen ändern. Die Karte zeigt danach eine andere Datei aus dem Inhaltsordner, die Dateien auf der Platte bleiben unverändert.
- Die virtuelle Tastatur lässt sich wie eine Karte verschieben, drehen und skalieren.
- Abhängigkeit `ffpyplayer` für Videowiedergabe, pytest für Tests der reinen Logik.
- Beispielinhalte im Ordner `inhalte/`: die vier Demobilder aus `touch-demo/bilder/`, ein Text und das Video `demo.mp4` aus `../folk-carthag/user-programs/carthag/video/`.

Nicht enthalten: Speichern der Kartenlage, Ersatzgesten für Single-Touch-Rahmen, neue Karten auf dem Tisch anlegen, Löschen von Karten.

## Verträglichkeit mit `inbetriebnahme-touchrahmen`

Grundsätzlich verträglich. Der Change ist noch nicht umgesetzt (0/27 Tasks). Drei Stellen müssen dort angepasst werden, bevor er umgesetzt wird:

1. **Kiosk-Start** (D8, Spec `tisch-einrichtung`, Requirement „Kiosk-Autostart per Schalter“): Die systemd-Unit startet `touch-demo/app.py`. Sie soll künftig `.venv/bin/python -m tisch` mit `WorkingDirectory=<projekt>` starten. Dasselbe gilt für die Szenarien „Mit Schalter“ und „Absturz der App“ sowie für Task 8.4.
2. **Python-Umgebung** (D10, Task 7.3): `setup.sh` installiert nur `kivy`. Für Videos fehlt `ffpyplayer`. `setup.sh` soll die Abhängigkeiten aus `pyproject.toml` übernehmen statt einer festen Liste.
3. **Kalibrier-Wirkung** (Spec `touch-kalibrierung`, Szenario „Wirkung auf die Tisch-App“): Es nennt `touch-demo/app.py`. Gemeint ist künftig die Tisch-App `python -m tisch`.

Ohne Konflikt:
- Eingabe über `hidinput`/`mtdev` und Kalibrierung in `~/.kivy/config.ini`: `tisch` liest nur, was Kivy daraus macht. Den Tastaturmodus setzt `tisch` nur im Speicher und schreibt `config.ini` nicht.
- `mouse = mouse,disable_on_activity` verhindert doppelte Ereignisse. Davon profitiert die Erkennung des langen Touchs.
- Vollbild über `KCFG_GRAPHICS_FULLSCREEN=auto`: `tisch` setzt kein Vollbild fest und läuft am Mac im Fenster.
- Die virtuelle Tastatur ist Teil der App. Cage braucht keine Bildschirmtastatur.
- pytest und `tests/` werden in beiden Changes gebraucht. Wer zuerst umgesetzt wird, legt sie an.

Abhängigkeit: Drehen und Skalieren setzen Multitouch voraus. Ob der LM-40IN unter Linux Multitouch liefert, klärt erst der Touchtest aus `inbetriebnahme-touchrahmen`. Bei Single-Touch lassen sich Karten im POC nur verschieben.

## Capabilities

### New Capabilities

- `karten-tisch`: Fläche mit frei beweglichen Karten. Multitouch-Gesten (verschieben, drehen, skalieren), Nachrutschen mit Reibung, Begrenzung auf die Fläche.
- `kartentypen`: Laden der Karten aus einem Inhaltsordner, Typen Text/Bild/Video und Erweiterung um weitere Typen.
- `karten-bearbeitung`: Bearbeitung per langem Touch, virtuelle Tastatur als bewegliches Element, Ändern von Textinhalt bzw. Dateiname, Zurückschreiben von Texten.

### Modified Capabilities

Keine. Es gibt noch keine Haupt-Specs. Die Anpassungen an `inbetriebnahme-touchrahmen` (siehe oben) erfolgen in jenem Change.

## Impact

- Neu: Paket `tisch/`, Ordner `inhalte/` mit Beispielinhalten (Video ca. 4 MB im Repo), Tests unter `tests/`.
- `pyproject.toml`: `ffpyplayer` als Abhängigkeit, pytest als Dev-Gruppe (falls noch nicht vorhanden).
- Change `inbetriebnahme-touchrahmen`: drei Anpassungen (Kiosk-Start, Abhängigkeiten in `setup.sh`, ein Szenario).
- Unverändert: `touch-demo/`, `~/.kivy/config.ini`.

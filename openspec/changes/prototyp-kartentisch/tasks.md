# Tasks

## 1. Gerüst und Abhängigkeiten

- [x] 1.1 Paket `tisch/` (`__init__.py`, `__main__.py`, `typen/__init__.py`) und `tests/` anlegen. In `pyproject.toml` `ffpyplayer` als Abhängigkeit und pytest als Poetry-Dev-Gruppe ergänzen (nur falls noch nicht vorhanden). Prüfen: `poetry install` gelingt, `poetry run python -c "import ffpyplayer"` läuft, `poetry run pytest` läuft ohne Fehler.
- [x] 1.2 Ordner `inhalte/` mit Beispielinhalten anlegen: die vier Bilder aus `touch-demo/bilder/` kopieren, `demo.mp4` aus `../folk-carthag/user-programs/carthag/video/` kopieren, `willkommen.txt` mit Umlauten und zwei Absätzen anlegen. Prüfen: `ls inhalte/` zeigt 6 Dateien, `file inhalte/demo.mp4` meldet MP4.

## 2. Inhalte und Registry (reine Logik)

- [x] 2.1 `tisch/typen/__init__.py` + `basis.py`: Registry mit `registriere`, `typ_fuer(pfad)` (Endung klein), `ValueError` bei doppelter Endung, `Kartentyp`-Basisklasse (D2). Prüfen: pytest für Zuordnung, Groß-/Kleinschreibung, doppelte Endung und Dummy-Typ für neue Endung.
- [x] 2.2 `tisch/inhalte.py`: `scanne(ordner)` liefert sortiert die unterstützten Dateien, ignoriert Unterordner und unbekannte Endungen, liefert bei fehlendem Ordner eine leere Liste. Prüfen: pytest mit `tmp_path` (gemischter Ordner, leerer Ordner, fehlender Ordner).
- [x] 2.3 `pruefe_dateiname(ordner, name, typ)` nach D3 mit eigener Meldung je Fall. Prüfen: pytest für gültig, fehlende Datei, `../x.png`, absoluten Pfad, Symlink nach außen und falschen Typ.
- [x] 2.4 `schreibe_text(pfad, text)` nach D4 (Schreibrecht prüfen, temporäre Datei + `os.replace`, UTF-8). Prüfen: pytest für Umlaute, schreibgeschützte Datei (Fehler, Inhalt unverändert), keine liegengebliebene temporäre Datei.

## 3. Karten und Tischfläche

- [x] 3.1 `tisch/karte.py`: `SchwungKarte` und `kartengroesse` aus `touch-demo/app.py` übernehmen. Die Karte erhält einen `Kartentyp` und einen Pfad, Skalierung 0,3–4. Prüfen: Karte am Mac per Maus ziehen, wischen und fangen. Sie rutscht nach und hält am Rand. Nach einer Rechtsklick-Zwei-Finger-Geste rutscht sie nicht nach.
- [x] 3.2 `tisch/typen/text.py` (Label mit Umbruch an der Kartenbreite, Hintergrund) und `bild.py` (Image `fit_mode="contain"`, Seitenverhältnis). Prüfen: `willkommen.txt` erscheint mit Umlauten umbrochen, Hochformat-Bild ist höher als breit.
- [x] 3.3 `tisch/typen/video.py` nach D8 (stumm, Schleife, Seitenverhältnis nach `on_texture`, Fehlererkennung nach 3 s). Prüfen: `demo.mp4` läuft stumm in Schleife und läuft beim Drehen weiter. Eine Datei mit Müllinhalt als `.mp4` ergibt eine Fehlerkarte.
- [x] 3.4 `tisch/app.py` + `__main__.py`: Argument `--inhalte` (Standard `<projekt>/inhalte`), Raster-Anordnung nach D9, Fehlerkarte und Hinweis bei leerem Ordner (D10), kein festes Vollbild. Prüfen: `poetry run python -m tisch` zeigt 6 Karten im Fenster. `--inhalte /tmp/leer` zeigt den Hinweis. `KCFG_GRAPHICS_FULLSCREEN=auto poetry run python -m tisch` startet im Vollbild.
- [x] 3.5 Erweiterbarkeit belegen: In einem Test wird ein Dummy-Kartentyp (z. B. `.md` als Label) registriert, ohne Code außerhalb des Tests zu ändern. Prüfen: pytest erzeugt über die App-Ladefunktion für eine `.md`-Datei eine `SchwungKarte` mit diesem Typ (ohne Fenster, Kivy-Widgets headless).

## 4. Langer Touch und Bearbeitung

- [x] 4.1 `tisch/langdruck.py`: Zustandsmaschine nach D5 (0,8 s, 10 dp, zweiter Finger bricht ab). Prüfen: pytest für Auslösen, Bewegen über der Schwelle, zweiten Finger, Loslassen vor Ablauf.
- [x] 4.2 Langdruck in `SchwungKarte` einbinden (Clock, Schwung stoppen, Touch freigeben, Rückruf an die Bearbeitung). Prüfen: Am Mac 1 s gedrückt halten öffnet eine Platzhalter-Bearbeitung. Kurzes Ziehen öffnet nichts.
- [x] 4.3 `tisch/tastatur.py` + Kivy-Config im Speicher in `__main__` (D6: `systemandmulti`, `qwertz`, `set_vkeyboard_class`). Prüfen: `~/.kivy/config.ini` ist nach dem Lauf unverändert (Prüfsumme vorher/nachher). Die Tastatur zeigt ä, ö, ü, ß.
- [x] 4.4 `tisch/bearbeitung.py`: Overlay in der Karte mit Eingabefeld, Übernehmen, Abbrechen und Fehlerzeile. Dazu „eine Bearbeitung gleichzeitig“ mit Hinweis auf der anderen Karte (D7) sowie Platzierung und Drehung der Tastatur neben der Karte. Prüfen: am Mac öffnen, abbrechen, zweite Karte lange drücken (Hinweis erscheint). Bei einer um 180° gedrehten Karte ist die Tastatur ebenfalls gedreht. Das Ziehen einer anderen Karte schließt die Tastatur nicht.
- [x] 4.5 Textkarte: `bearbeitungswert`/`uebernehme` mit `schreibe_text`, Fehlerzeile bei schreibgeschützter Datei. Prüfen: „Größe“ über die virtuelle Tastatur tippen und übernehmen. Die Karte und `inhalte/willkommen.txt` enthalten es auch nach einem Neustart. Mit `chmod a-w` bleibt die Bearbeitung mit Hinweis offen.
- [x] 4.6 Bild-/Videokarte: Dateiname wechseln über `pruefe_dateiname`, Kartengröße an das neue Seitenverhältnis anpassen, Lage und Drehung erhalten. Prüfen: Ein anderes Bild erscheint. Ein falscher Name, `../x.png` und ein Videoname in einer Bildkarte werden mit Hinweis abgelehnt. `git status inhalte/` zeigt keine Änderungen.
- [x] 4.7 Tastatur beweglich: Ziehen am Rand, Drehen und Skalieren ohne Tastenauslösung, kein Nachrutschen. Prüfen: am Mac per Rand ziehen und mit Rechtsklick drehen. Im Feld erscheint dabei kein Zeichen, danach lässt sich normal tippen.

## 5. Dokumentation und Abstimmung

- [x] 5.1 README-Abschnitt „Tisch-App (Prototyp)“: Start, `--inhalte`, Kartentypen, Langdruck/Bearbeitung, Anleitung „Neuen Kartentyp hinzufügen“ (Klasse + `registriere`). Prüfen: Die Befehle im README laufen am Mac wie beschrieben.
- [x] 5.2 Change `inbetriebnahme-touchrahmen` per `/opsx:update` anpassen: Kiosk-Unit startet `.venv/bin/python -m tisch` mit `WorkingDirectory` (D8, Spec `tisch-einrichtung`, Task 8.4). `setup.sh` installiert die Abhängigkeiten aus `pyproject.toml` (D10, Task 7.3). Das Szenario „Wirkung auf die Tisch-App“ nennt `python -m tisch`. Prüfen: `openspec validate inbetriebnahme-touchrahmen` ohne Fehler, `grep -r "touch-demo/app.py" openspec/changes/inbetriebnahme-touchrahmen` findet nur noch den Hinweis, dass `touch-demo` unverändert bleibt.

## 6. Abnahme am Tisch

- [ ] 6.1 Auf dem Tischrechner (nach `inbetriebnahme`) `python -m tisch` unter cage starten. Prüfen: Alle 6 Karten erscheinen, das Video läuft, zwei Personen ziehen gleichzeitig verschiedene Karten.
- [ ] 6.2 Multitouch-Gesten und Langdruck am Rahmen. Prüfen: Drehen und Skalieren mit zwei Fingern funktionieren (falls der Touchtest Multitouch ergab). Langdruck öffnet zuverlässig, ohne Fehlauslösung durch Geistertouches. Gegebenenfalls die Schwellen in `langdruck.py` anpassen und notieren.
- [ ] 6.3 Bearbeitung am Rahmen. Prüfen: Text über die virtuelle Tastatur ändern und übernehmen, die Tastatur verschieben, drehen und skalieren. Die Startgröße der Tastatur für 40" festlegen (Open Question in design.md).

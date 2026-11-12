# Tasks

## 1. Projektgerüst

- [ ] 1.1 Paket `inbetrieb/` (`__init__.py`, `__main__.py`) und `tests/` anlegen, pytest als Poetry-Dev-Gruppe in `pyproject.toml` ergänzen; prüfen: `poetry run pytest` läuft (0 Tests, kein Fehler)

## 2. Geräteerkennung (`inbetrieb/geraet.py`, nur Standardbibliothek)

- [ ] 2.1 abs-Bitmaske aus sysfs parsen (Multitouch, Typ A/B, INPUT_PROP_DIRECT); prüfen: pytest mit Fixture-Verzeichnissen für Typ A, Typ B, Single-Touch und Touchpad
- [ ] 2.2 stabilen Pfad ermitteln (by-id → by-path → eventX mit Warnung), mehrere Kandidaten melden; prüfen: pytest mit Fixture-Symlinks
- [ ] 2.3 CLI `python3 -m inbetrieb.geraet` mit maschinenlesbarer Ausgabe (Pfad, Provider hidinput/mtdev, Typ, Warnungen) und Exit-Code 1 ohne Gerät; prüfen: pytest ruft die CLI gegen Fixture-Root auf

## 3. Konfiguration (`inbetrieb/kivyconfig.py`, nur Standardbibliothek)

- [ ] 3.1 `[input] touch` und `mouse = mouse,disable_on_activity` setzen, dabei rotation/invert eines bestehenden Eintrags übernehmen und `[postproc:calibration]` sowie fremde Einträge unverändert lassen; prüfen: pytest (Kalibrierung bleibt beim erneuten Schreiben gleich)
- [ ] 3.2 Kalibrierung schreiben (rotation/invert in `[input] touch`, ratio/offset in `[postproc:calibration]`) mit vorheriger Sicherung `config.ini.bak`; prüfen: pytest (Sicherung enthält alten Inhalt)
- [ ] 3.3 CLI `python3 -m inbetrieb.kivyconfig input <pfad> <provider>` für `setup.sh`; prüfen: pytest gegen temporäres `KIVY_HOME`

## 4. Kalibrier-Mathematik (`inbetrieb/kalibrierung.py`)

- [ ] 4.1 Kivy-Transformationskette (Normierung → invert → rotation → postproc) als Funktion nachbilden und gegen `kivy/input/providers/hidinput.py` + `postproc/calibration.py` abgleichen; prüfen: pytest vergleicht mit Kivys eigenen Formeln an Stichproben
- [ ] 4.2 Ausrichtung aus 4 Punkten bestimmen (8 Kombinationen, kanonische Form); prüfen: pytest mit konstruierten Punkten für gespiegeltes Y, vertauschte Achsen, 180°
- [ ] 4.3 lineare Regression je Achse → ratio/offset, Fehlerfunktion für das Kontrollkreuz (Pixel, Schwelle 2 % Diagonale); prüfen: pytest mit „Rahmen größer als Bild“ (ratio > 1) und Rauschen

## 5. Bericht (`inbetrieb/bericht.py`)

- [ ] 5.1 Datenklasse mit Gerät, Maximum, Abdeckung, Geistertouches, Abweichungen, doppelten Ereignissen; JSON nach `~/.local/state/dyndesktop/touchtest-<zeitstempel>.json`; prüfen: pytest (Datei entsteht, Felder vollständig, Name mit Zeitstempel)

## 6. Kivy-App (`inbetrieb/app.py`, `__main__.py`)

- [ ] 6.1 Einstieg mit Argumenten `--kalibrieren`/`--touchtest`, Rohmodus per In-Memory-Override vor Kivy-Window-Import, Vollbild, Neustart per `os.execv`; prüfen: `python -m inbetrieb --kalibrieren` am Mac startet ohne Fehler und `~/.kivy/config.ini` ist danach unverändert
- [ ] 6.2 Menü-Screen (Kalibrieren, Touchtest, Beenden), große Touch-Knöpfe, Zurück-Element in jedem Modus; prüfen: am Mac per Maus durch alle Modi und zurück navigieren
- [ ] 6.3 Kalibrier-Screen: 4 Kreuze, Mehrfinger-Erfassung verwerfen, Kontrollkreuz mit vorläufiger Korrektur, Abweichung + Speichern/Wiederholen, Speichern → Sicherung + execv `--touchtest`; prüfen: am Mac mit simulierten Klicks durchlaufen, `config.ini` enthält die Werte und `config.ini.bak` existiert
- [ ] 6.4 Touchtest-Screen: Markierung + Farbe + ID pro Touch, aktuelle Anzahl/Maximum, Spuren, Zurücksetzen; prüfen: am Mac per Rechtsklick (Kivy-Multitouch-Simulation) mehrere Touches erzeugen, Maximum steigt
- [ ] 6.5 Heatmap 16×9, Ruhephase (10/30/60 s) mit Geistertouch-Zählung und Markierung, Zielpunkte mit Abweichung, Hinweis auf Maus-Duplikate; prüfen: am Mac Ruhephase ohne Klick ergibt 0, Klick während der Phase zählt als 1
- [ ] 6.6 Bericht beim Verlassen schreiben und Pfad anzeigen; prüfen: nach dem Verlassen liegt eine neue JSON-Datei vor

## 7. Einrichtungsskript (`setup.sh`)

- [ ] 7.1 Grundgerüst: Abbruch bei root, Projektverzeichnis aus Skriptpfad, Prüfpunkt-Sammlung und Abschlussbericht OK/FEHLT mit Exit-Code; prüfen: `shellcheck setup.sh` ohne Befund, Aufruf mit `sudo` bricht ab
- [ ] 7.2 apt-Pakete (cage, wlr-randr, xwayland, evtest, libinput-tools, python3-venv) nur bei Bedarf installieren, Benutzer zur Gruppe `input` mit Hinweis auf Neuanmeldung; prüfen: zweiter Lauf installiert nichts und meldet OK
- [ ] 7.3 `.venv` anlegen/aktualisieren und Kivy installieren; prüfen: `.venv/bin/python -c "import kivy"` gelingt
- [ ] 7.4 Gerät über `python3 -m inbetrieb.geraet` erkennen, Single-Touch-Warnung, Konfiguration über `python3 -m inbetrieb.kivyconfig` schreiben; prüfen: ohne Gerät FEHLT + Exit ≠ 0; mit Gerät enthält `config.ini` den by-id-Pfad
- [ ] 7.5 systemd-Unit `dyndesktop-kiosk.service` (cage `-s -m last`, `KCFG_GRAPHICS_FULLSCREEN=auto`, `Restart=always`, `RestartSec=2`, Conflicts getty@tty1) ablegen; mit `--kiosk` aktivieren, ohne deaktivieren; prüfen: `systemctl is-enabled dyndesktop-kiosk` liefert jeweils enabled bzw. disabled
- [ ] 7.6 README-Abschnitt „Inbetriebnahme“ (Debian netinst, `git clone`, `./setup.sh`, Testmodus `cage -s -- .venv/bin/python -m inbetrieb`, `--kiosk`, Rückweg); prüfen: die Befehle im README entsprechen den tatsächlichen Pfaden und Schaltern

## 8. Abnahme am Gerät

- [ ] 8.1 Laptop mit Debian 13 Live/Installation: `setup.sh` zweimal ausführen; prüfen: zweiter Lauf komplett OK, Exit 0
- [ ] 8.2 LMENGER-Rahmen anschließen, Touchtest: Maximum gleichzeitiger Touches, Heatmap, Ruhephase 60 s; prüfen: Bericht-JSON liegt vor und ist per SSH abholbar (Entscheidung zur Rückgabe treffen)
- [ ] 8.3 Kalibrieren und anschließend Zielpunkte im Touchtest; prüfen: größte Abweichung unter 2 % der Diagonale, `touch-demo/app.py` folgt dem Finger
- [ ] 8.4 NUC: `setup.sh --kiosk`, Neustart; prüfen: `touch-demo/app.py` erscheint im Vollbild, nach `pkill -f touch-demo/app.py` startet sie neu, Strg+Alt+F2 erreicht die Textkonsole

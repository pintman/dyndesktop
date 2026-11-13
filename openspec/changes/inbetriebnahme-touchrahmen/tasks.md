# Tasks

## 1. Projektgerüst

- [ ] 1.1 Paket `inbetrieb/` (`__init__.py`, `__main__.py`) und `tests/` anlegen, pytest als Poetry-Dev-Gruppe in `pyproject.toml` ergänzen; prüfen: `poetry run pytest` läuft (0 Tests, kein Fehler)

## 2. Geräteerkennung (`inbetrieb/geraet.py`, nur Standardbibliothek)

- [ ] 2.1 abs-Bitmaske aus sysfs parsen (Multitouch, Typ A/B, INPUT_PROP_DIRECT); prüfen: pytest mit Fixture-Verzeichnissen für Typ A, Typ B, Single-Touch und Touchpad
- [ ] 2.2 stabilen Pfad ermitteln (by-id → by-path → eventX mit Warnung), mehrere Kandidaten melden; prüfen: pytest mit Fixture-Symlinks
- [ ] 2.3 CLI `python3 -m inbetrieb.geraet` mit maschinenlesbarer Ausgabe (Pfad, Provider hidinput/mtdev, Typ, Warnungen) und Exit-Code 1 ohne Gerät; prüfen: pytest ruft die CLI gegen Fixture-Root auf

## 3. Konfiguration (`inbetrieb/kivyconfig.py`, `inbetrieb/niriconfig.py`, nur Standardbibliothek)

- [ ] 3.1 `[input] touch` und `mouse = mouse,disable_on_activity` setzen, dabei rotation/invert eines bestehenden Eintrags übernehmen und `[postproc:calibration]` sowie fremde Einträge unverändert lassen; prüfen: pytest (Kalibrierung bleibt beim erneuten Schreiben gleich)
- [ ] 3.2 Kalibrierung schreiben (rotation/invert in `[input] touch`, ratio/offset in `[postproc:calibration]`) mit vorheriger Sicherung `config.ini.bak`; prüfen: pytest (Sicherung enthält alten Inhalt)
- [ ] 3.3 CLI `python3 -m inbetrieb.kivyconfig input <pfad> <provider>` für `setup.sh`; prüfen: pytest gegen temporäres `KIVY_HOME`
- [ ] 3.4 `niriconfig.py`: `config.kdl` aus Vorlage erzeugen (D12: gaps 0, struts, focus-ring/border aus, `open-maximized`, `prefer-no-csd`, `touch { off }`, Cursor ausblenden, `scale 1`, `spawn-at-startup kiosk.sh`), struts aus bestehender Datei übernehmen (ohne Datei 0), Sicherung `config.kdl.bak`; prüfen: pytest (struts bleiben beim Neuschreiben gleich, Sicherung enthält alten Inhalt)
- [ ] 3.5 interne Ausgänge über `/sys/class/drm/card*-{eDP,LVDS,DSI}-*` finden und als `output "<name>" { off; }` eintragen; prüfen: pytest mit Fixture-Verzeichnis (Laptop mit eDP-1 + HDMI-A-1, NUC nur HDMI)
- [ ] 3.6 Funktion `struts setzen/lesen` für den Flächen-Screen und CLI `python3 -m inbetrieb.niriconfig schreiben <projekt>` für `setup.sh`; prüfen: pytest gegen temporäres `XDG_CONFIG_HOME`; ist niri installiert, besteht die erzeugte Datei `niri validate`

## 4. Kalibrier-Mathematik (`inbetrieb/kalibrierung.py`)

- [ ] 4.1 Kivy-Transformationskette (Normierung → invert → rotation → postproc) als Funktion nachbilden und gegen `kivy/input/providers/hidinput.py` + `postproc/calibration.py` abgleichen; prüfen: pytest vergleicht mit Kivys eigenen Formeln an Stichproben
- [ ] 4.2 Ausrichtung aus 4 Punkten bestimmen (8 Kombinationen, kanonische Form); prüfen: pytest mit konstruierten Punkten für gespiegeltes Y, vertauschte Achsen, 180°
- [ ] 4.3 lineare Regression je Achse → ratio/offset, Fehlerfunktion für das Kontrollkreuz (Pixel, Schwelle 2 % Fensterdiagonale); prüfen: pytest mit „Rahmen größer als Bild“ (ratio > 1), „Rahmen kleiner als Fenster“ (ratio < 1) und Rauschen

## 5. Bericht (`inbetrieb/bericht.py`)

- [ ] 5.1 Datenklasse mit Gerät, Maximum, Abdeckung, Geistertouches, Abweichungen, doppelten Ereignissen; JSON nach `~/.local/state/dyndesktop/touchtest-<zeitstempel>.json`; prüfen: pytest (Datei entsteht, Felder vollständig, Name mit Zeitstempel)

## 6. Kivy-App (`inbetrieb/app.py`, `__main__.py`)

- [ ] 6.1 Einstieg mit Argumenten `--flaeche`/`--kalibrieren`/`--touchtest`, Rohmodus per In-Memory-Override vor Kivy-Window-Import, kein Vollbild, Neustart per `os.execv`; prüfen: `python -m inbetrieb --kalibrieren` am Mac startet im Fenster ohne Fehler und `~/.kivy/config.ini` ist danach unverändert
- [ ] 6.2 Menü-Screen (Fläche, Kalibrieren, Touchtest, Beenden), große Touch-Knöpfe, Zurück-Element in Kalibrier- und Testmodus, Hinweis „neu kalibrieren“ nach geänderter Fläche, Beenden beendet unter niri auch niri (`niri msg action quit --skip-confirmation`, nur wenn `NIRI_SOCKET` gesetzt); prüfen: am Mac per Maus durch alle Modi und zurück navigieren
- [ ] 6.3 Flächen-Screen (D13): Rand an den Fensterkanten, Tab wählt Kante, Pfeiltasten ±1 px (Umschalt ±10 px) schreiben struts über `niriconfig`, Enter übernimmt, Esc stellt Startwerte wieder her; prüfen: am Mac mit temporärem `XDG_CONFIG_HOME` ändern Tasten die struts in `config.kdl`, Esc stellt sie wieder her
- [ ] 6.4 Kalibrier-Screen: 4 Kreuze nahe den Fensterecken, Mehrfinger-Erfassung verwerfen, Kontrollkreuz mit vorläufiger Korrektur, Abweichung + Speichern/Wiederholen, Speichern → Sicherung + execv `--touchtest`; prüfen: am Mac mit simulierten Klicks durchlaufen, `config.ini` enthält die Werte und `config.ini.bak` existiert
- [ ] 6.5 Touchtest-Screen: Markierung + Farbe + ID pro Touch, aktuelle Anzahl/Maximum, Spuren, Zurücksetzen; prüfen: am Mac per Rechtsklick (Kivy-Multitouch-Simulation) mehrere Touches erzeugen, Maximum steigt
- [ ] 6.6 Heatmap 16×9, Ruhephase (10/30/60 s) mit Geistertouch-Zählung und Markierung, Zielpunkte mit Abweichung, Hinweis auf Maus-Duplikate; prüfen: am Mac Ruhephase ohne Klick ergibt 0, Klick während der Phase zählt als 1
- [ ] 6.7 Bericht beim Verlassen schreiben und Pfad anzeigen; prüfen: nach dem Verlassen liegt eine neue JSON-Datei vor

## 7. Einrichtungsskript (`setup.sh`, `kiosk.sh`)

- [ ] 7.1 Grundgerüst: Abbruch bei root, Projektverzeichnis aus Skriptpfad, Prüfpunkt-Sammlung und Abschlussbericht OK/FEHLT mit Exit-Code; prüfen: `shellcheck setup.sh` ohne Befund, Aufruf mit `sudo` bricht ab
- [ ] 7.2 apt-Pakete (evtest, libinput-tools, python3-venv) nur bei Bedarf installieren, Benutzer zur Gruppe `input` mit Hinweis auf Neuanmeldung; prüfen: zweiter Lauf installiert nichts und meldet OK
- [ ] 7.3 niri (D11): `NIRI_VERSION` festlegen (MSRV, Optionsnamen aus 3.4 gegen deren Doku prüfen), apt-Paket falls vorhanden, sonst Build-Abhängigkeiten per apt, ggf. rustup, `cargo install --locked` nach `/usr/local/bin/niri`; Build nur bei abweichender Version; prüfen: `niri --version` meldet `NIRI_VERSION`, zweiter Lauf baut nicht neu
- [ ] 7.4 `.venv` anlegen/aktualisieren und die Abhängigkeiten aus `pyproject.toml` (`[project].dependencies`, per `tomllib`) installieren; prüfen: `.venv/bin/python -c "import kivy, ffpyplayer"` gelingt
- [ ] 7.5 Gerät über `python3 -m inbetrieb.geraet` erkennen, Single-Touch-Warnung, Kivy-Konfiguration über `python3 -m inbetrieb.kivyconfig` und niri-Konfiguration über `python3 -m inbetrieb.niriconfig` schreiben; prüfen: ohne Gerät FEHLT + Exit ≠ 0; mit Gerät enthält `config.ini` den by-id-Pfad; `config.kdl` existiert, eingestellte struts bleiben beim zweiten Lauf erhalten
- [ ] 7.6 `kiosk.sh`: `SDL_VIDEODRIVER=wayland`, mit `DYNDESKTOP_KIOSK=1` Endlosschleife um `.venv/bin/python -m tisch` (2 s Pause), mit `DYNDESKTOP_START=<modul>` einmaliger Start, sonst nichts; prüfen: `shellcheck kiosk.sh` ohne Befund; Testmodus `DYNDESKTOP_START=inbetrieb niri` auf tty1 zeigt das Menü maximiert in der Rahmenfläche
- [ ] 7.7 Fallback Xwayland: startet Kivy nicht nativ unter Wayland, `xwayland-satellite` bauen und `SDL_VIDEODRIVER` weglassen; prüfen: App erscheint unter niri, Ergebnis im README vermerkt
- [ ] 7.8 systemd-Unit `dyndesktop-kiosk.service` (D8: `WorkingDirectory=<projekt>`, `Environment=DYNDESKTOP_KIOSK=1`, `ExecStart=<niri>`, `Restart=always`, `RestartSec=2`, Conflicts getty@tty1, kein `KCFG_GRAPHICS_FULLSCREEN`) ablegen; mit `--kiosk` aktivieren, ohne deaktivieren; prüfen: `systemctl is-enabled dyndesktop-kiosk` liefert jeweils enabled bzw. disabled
- [ ] 7.9 README-Abschnitt „Inbetriebnahme“ (Debian netinst, `git clone`, `./setup.sh`, Testmodus `DYNDESKTOP_START=inbetrieb niri`, Fläche einstellen, Notweg struts per SSH in `~/.config/niri/config.kdl`, `--kiosk`, Rückweg); prüfen: die Befehle im README entsprechen den tatsächlichen Pfaden und Schaltern

## 8. Abnahme am Gerät

- [ ] 8.1 Laptop mit Debian 13 Live/Installation: `setup.sh` zweimal ausführen; prüfen: zweiter Lauf komplett OK, Exit 0, niri nicht erneut gebaut
- [ ] 8.2 Beamer anschließen, Keystone am Beamer einstellen, Testmodus starten; prüfen: eingebauter Bildschirm aus, Menü auf dem Beamerbild
- [ ] 8.3 Fläche einstellen; prüfen: Fensterkanten liegen auf der Innenkante des Rahmens, Rest des Beamerbilds schwarz, Werte nach Neustart von niri erhalten
- [ ] 8.4 LMENGER-Rahmen anschließen, Touchtest bei laufendem Beamer: Maximum gleichzeitiger Touches, Heatmap, Ruhephase 60 s; prüfen: Bericht-JSON liegt vor und ist per SSH abholbar (Entscheidung zur Rückgabe treffen)
- [ ] 8.5 Kalibrieren und anschließend Zielpunkte im Touchtest; prüfen: größte Abweichung unter 2 % der Fensterdiagonale, die Tisch-App (`python -m tisch`) folgt dem Finger
- [ ] 8.6 NUC: `setup.sh --kiosk`, Neustart; prüfen: `python -m tisch` erscheint in der Rahmenfläche, nach `pkill -f 'python -m tisch'` startet sie neu, Strg+Alt+F2 erreicht die Textkonsole

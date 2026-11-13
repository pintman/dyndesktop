# Spec Delta

## Purpose

Richtet einen frischen Debian-Rechner (Intel NUC oder Laptop) per Skript als Touch-Tisch ein, wiederholbar und mit klarer Rückmeldung, was fehlt.

## ADDED Requirements

### Requirement: Wiederholbare Ausführung
Das Einrichtungsskript SHALL beliebig oft hintereinander ausführbar sein. Ein erneuter Lauf auf einem bereits eingerichteten System SHALL keine Änderungen vornehmen außer fehlenden Schritten und SHALL keine Fehler erzeugen.

#### Scenario: Zweiter Lauf ohne Änderungen
- **WHEN** das Skript auf einem vollständig eingerichteten System erneut ausgeführt wird
- **THEN** meldet es alle Prüfpunkte als OK und endet mit Exit-Code 0

#### Scenario: Abgebrochener erster Lauf
- **WHEN** ein Lauf in der Mitte abgebrochen und das Skript danach erneut gestartet wird
- **THEN** holt es die fehlenden Schritte nach, ohne bereits erledigte doppelt anzulegen

### Requirement: Abschlussbericht
Das Skript SHALL am Ende für jeden Prüfpunkt (Pakete, Gruppe `input`, Python-Umgebung, Touch-Gerät, Kivy-Konfiguration, Autostart) den Zustand OK oder FEHLT ausgeben. Es SHALL mit einem Exit-Code ungleich 0 enden, wenn ein Pflicht-Prüfpunkt FEHLT.

#### Scenario: Kein Touch-Gerät angeschlossen
- **WHEN** das Skript läuft und kein Touch-Gerät angeschlossen ist
- **THEN** meldet es den Prüfpunkt Touch-Gerät als FEHLT mit einem Hinweis zum Anschluss und endet mit Exit-Code ungleich 0

### Requirement: Systempakete und Rechte
Das Skript SHALL die für Kompositor, Diagnose und Python-Umgebung nötigen Pakete installieren und den aufrufenden Benutzer der Gruppe `input` hinzufügen. Ist die Gruppenzugehörigkeit neu, SHALL es darauf hinweisen, dass eine Neuanmeldung nötig ist.

#### Scenario: Benutzer neu in Gruppe input
- **WHEN** der Benutzer vor dem Lauf nicht in der Gruppe `input` war
- **THEN** fügt das Skript ihn hinzu und weist auf die nötige Neuanmeldung hin

#### Scenario: Aufruf als root
- **WHEN** das Skript direkt als root gestartet wird
- **THEN** bricht es mit einer Meldung ab, dass es als normaler Benutzer zu starten ist

### Requirement: Python-Umgebung
Das Skript SHALL im Projektverzeichnis eine eigene Python-Umgebung mit den Abhängigkeiten aus `pyproject.toml` anlegen bzw. aktualisieren, aus der das Inbetriebnahme-Programm und die Tisch-App (`python -m tisch`) gestartet werden können.

#### Scenario: Kivy verfügbar
- **WHEN** das Skript erfolgreich gelaufen ist
- **THEN** lässt sich Kivy mit dem Python-Interpreter der Umgebung importieren

#### Scenario: Videowiedergabe verfügbar
- **WHEN** das Skript erfolgreich gelaufen ist
- **THEN** lässt sich `ffpyplayer` mit dem Python-Interpreter der Umgebung importieren

### Requirement: Erkennung des Touch-Geräts
Das Skript SHALL das angeschlossene Multitouch-Gerät über einen stabilen Pfad unter `/dev/input/by-id/` ermitteln und feststellen, ob es das Multitouch-Protokoll Typ A oder Typ B verwendet. Meldet das Gerät keine Multitouch-Achsen, SHALL das Skript ausdrücklich warnen, dass nur Single-Touch möglich ist.

#### Scenario: Typ-B-Gerät
- **WHEN** das Gerät Multitouch-Slots meldet
- **THEN** wählt das Skript den Eingabeweg `hidinput` mit dem by-id-Pfad

#### Scenario: Typ-A-Gerät
- **WHEN** das Gerät Multitouch-Positionen, aber keine Slots meldet
- **THEN** wählt das Skript den Eingabeweg `mtdev` mit dem by-id-Pfad

#### Scenario: Nur Single-Touch
- **WHEN** das Gerät keine Multitouch-Achsen meldet
- **THEN** gibt das Skript eine deutliche Warnung „nur Single-Touch“ aus

### Requirement: Kivy-Eingabekonfiguration
Das Skript SHALL in der Kivy-Konfiguration des Benutzers den ermittelten Eingabeweg eintragen und doppelte Mausereignisse unterdrücken. Bestehende Kalibrierwerte und andere Einträge SHALL es dabei unverändert lassen.

#### Scenario: Kalibrierung bleibt erhalten
- **WHEN** eine Kalibrierung gespeichert ist und das Skript erneut läuft
- **THEN** sind die Kalibrierwerte nach dem Lauf unverändert

#### Scenario: Keine doppelten Ereignisse
- **WHEN** die Konfiguration geschrieben ist und ein Finger die Fläche berührt
- **THEN** kommt in Kivy genau ein Touch-Ereignis an, kein zusätzliches Mausereignis

### Requirement: Kiosk-Autostart per Schalter
Mit dem Schalter `--kiosk` SHALL das Skript einen Autostart einrichten und aktivieren: Nach dem Booten startet ohne Anmeldung der Kiosk-Kompositor mit der Tisch-App (`python -m tisch`) im Vollbild. Stürzt die App ab, wird sie neu gestartet. Ohne den Schalter SHALL kein Autostart aktiv sein.

#### Scenario: Ohne Schalter
- **WHEN** das Skript ohne `--kiosk` läuft
- **THEN** startet nach einem Neustart keine App automatisch, und ein früher eingerichteter Autostart ist deaktiviert

#### Scenario: Mit Schalter
- **WHEN** das Skript mit `--kiosk` gelaufen ist und der Rechner neu startet
- **THEN** erscheint die Tisch-App (`python -m tisch`) im Vollbild auf dem Tisch-Bildschirm

#### Scenario: Absturz der App
- **WHEN** die App im Kiosk-Betrieb abstürzt
- **THEN** wird sie automatisch neu gestartet

#### Scenario: Debug-Zugang
- **WHEN** der Kiosk-Betrieb läuft und eine Tastatur angeschlossen ist
- **THEN** ist ein Wechsel auf eine Textkonsole möglich

### Requirement: Laptop mit eingebautem Bildschirm
Auf einem Rechner mit mehreren Bildschirmen SHALL die gestartete App auf dem externen Tisch-Bildschirm erscheinen, und die Touch-Koordinaten SHALL sich auf dieses App-Fenster beziehen.

#### Scenario: Laptop mit HDMI-Fernseher
- **WHEN** ein Laptop mit angeschlossenem HDMI-Fernseher die App startet
- **THEN** läuft die App im Vollbild auf dem Fernseher, und ein Touch auf dem Rahmen trifft die entsprechende Stelle im App-Fenster

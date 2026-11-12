# Spec Delta

## Purpose

Misst interaktiv, was der Touchrahmen tatsächlich leistet – gleichzeitige Touches, Abdeckung, Geistertouches, Genauigkeit – und hält das Ergebnis als Bericht fest.

## ADDED Requirements

### Requirement: Anzeige gleichzeitiger Touches
Der Touchtest SHALL jeden aktiven Touch mit seiner Touch-ID und einer eigenen Farbe als Markierung anzeigen. Er SHALL die aktuelle Anzahl gleichzeitiger Touches und das bisherige Maximum laufend anzeigen.

#### Scenario: Mehrere Finger
- **WHEN** fünf Finger gleichzeitig auf der Fläche liegen
- **THEN** zeigt der Test fünf unterschiedlich gefärbte Markierungen mit verschiedenen IDs, die aktuelle Anzahl 5 und ein Maximum von mindestens 5

#### Scenario: Nur Single-Touch
- **WHEN** der Rahmen nur einen Touch gleichzeitig meldet
- **THEN** bleibt das Maximum bei 1, auch wenn mehrere Finger aufliegen

### Requirement: Spuren
Der Touchtest SHALL die Bewegung jedes Touches als Spur in seiner Farbe zeichnen, bis die Anzeige zurückgesetzt wird.

#### Scenario: Wischen
- **WHEN** ein Finger über die Fläche gezogen wird
- **THEN** bleibt eine durchgehende Spur in der Farbe dieses Touches sichtbar

#### Scenario: Zurücksetzen
- **WHEN** das Zurücksetzen-Element berührt wird
- **THEN** werden Spuren, Heatmap und Maximum gelöscht

### Requirement: Heatmap der Abdeckung
Der Touchtest SHALL die Fläche in ein Raster einteilen und Rasterfelder, in denen bereits Touch-Ereignisse ankamen, sichtbar von unberührten Feldern unterscheiden.

#### Scenario: Tote Zone
- **WHEN** die gesamte Fläche überstrichen wurde, ein Bereich aber keine Ereignisse liefert
- **THEN** bleiben die Rasterfelder dieses Bereichs als unberührt erkennbar

### Requirement: Geistertouch-Messung
Der Touchtest SHALL eine Ruhephase von wählbarer Dauer anbieten, in der niemand die Fläche berührt. Er SHALL alle in dieser Phase eintreffenden Touches als Geistertouches zählen, mit Position markieren und das Ergebnis anzeigen.

#### Scenario: Ruhige Umgebung
- **WHEN** die Ruhephase ohne Berührung abläuft und keine Ereignisse eintreffen
- **THEN** meldet der Test 0 Geistertouches

#### Scenario: Störlicht
- **WHEN** während der Ruhephase Touches ohne Berührung eintreffen
- **THEN** meldet der Test deren Anzahl und markiert ihre Positionen

### Requirement: Genauigkeitsprüfung
Der Touchtest SHALL Zielpunkte an Ecken, Rändern und in der Mitte anbieten und für jeden angetippten Zielpunkt die Abweichung in Pixeln sowie die größte Abweichung anzeigen.

#### Scenario: Ziel angetippt
- **WHEN** ein Zielpunkt angetippt wird
- **THEN** zeigt der Test die Abweichung zwischen Ziel und gemeldetem Touch in Pixeln

### Requirement: Doppelte Ereignisse erkennen
Der Touchtest SHALL anzeigen, wenn zu einer Berührung zusätzlich ein Mausereignis eintrifft.

#### Scenario: Maus-Duplikat
- **WHEN** eine Berührung sowohl als Touch als auch als Mausereignis ankommt
- **THEN** zeigt der Test einen Hinweis auf doppelte Ereignisse

### Requirement: Bericht
Beim Verlassen des Touchtests SHALL das Programm einen Bericht als JSON-Datei mit Zeitstempel im Namen speichern. Er enthält Gerät, Maximum gleichzeitiger Touches, Abdeckung, Geistertouches, Abweichungen und doppelte Ereignisse. Der Speicherort SHALL angezeigt werden, damit die Datei per SSH abholbar ist.

#### Scenario: Bericht nach Test
- **WHEN** der Touchtest über das Zurück-Element verlassen wird
- **THEN** existiert eine neue JSON-Datei mit den gemessenen Werten, und ihr Pfad wurde angezeigt

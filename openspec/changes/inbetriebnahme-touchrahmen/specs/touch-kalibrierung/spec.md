# Spec Delta

## Purpose

Bringt die Touch-Koordinaten des Rahmens interaktiv mit dem angezeigten Bild in Deckung und speichert die Korrektur dauerhaft für alle Kivy-Apps des Tisches.

## ADDED Requirements

### Requirement: Menü des Inbetriebnahme-Programms
Das Inbetriebnahme-Programm SHALL beim Start ein per Touch bedienbares Menü mit den Punkten Kalibrieren, Touchtest und Beenden im Vollbild anzeigen. Jeder Modus SHALL eine per Touch erreichbare Möglichkeit bieten, ins Menü zurückzukehren.

#### Scenario: Programmstart
- **WHEN** das Programm ohne Argumente gestartet wird
- **THEN** zeigt es das Menü mit den drei Punkten

#### Scenario: Rückkehr ins Menü
- **WHEN** im Kalibrier- oder Testmodus das Zurück-Element berührt wird
- **THEN** erscheint wieder das Menü, ohne dass Kalibrierwerte gespeichert werden

### Requirement: Erfassung der Kalibrierpunkte
Der Kalibriermodus SHALL nacheinander vier Zielkreuze nahe den Bildecken anzeigen und je Kreuz eine Berührung erfassen. Dabei SHALL er die Werte ohne bisherige Kalibrierkorrektur auswerten, damit eine falsche alte Kalibrierung das Ergebnis nicht verfälscht.

#### Scenario: Vier Punkte erfasst
- **WHEN** die vier Kreuze nacheinander angetippt wurden
- **THEN** berechnet das Programm die Korrektur und zeigt ein fünftes Kontrollkreuz in der Bildmitte

#### Scenario: Mehrfinger-Berührung beim Kalibrieren
- **WHEN** während der Erfassung mehrere Finger gleichzeitig auf der Fläche liegen
- **THEN** verwirft das Programm diese Erfassung und fordert erneut zum Antippen desselben Kreuzes auf

### Requirement: Ermittlung von Ausrichtung und Korrektur
Aus den vier Punkten SHALL das Programm ermitteln, ob die Touch-Achsen gegenüber dem Bild vertauscht oder gespiegelt sind, und je Achse einen Skalierungsfaktor und einen Versatz berechnen.

#### Scenario: Gespiegelte Y-Achse
- **WHEN** die Touch-Y-Werte gegenläufig zu den Bild-Y-Werten der Kreuze verlaufen
- **THEN** enthält das Ergebnis eine Spiegelung der Y-Achse

#### Scenario: Vertauschte Achsen
- **WHEN** die Touch-X-Werte mit der Bild-Y-Position der Kreuze zusammenhängen statt mit der Bild-X-Position
- **THEN** enthält das Ergebnis eine Drehung um 90 oder 270 Grad

#### Scenario: Rahmen größer als Bild
- **WHEN** die Touch-Werte der Kreuze einen kleineren Bereich abdecken als die Bildpositionen
- **THEN** ist der berechnete Skalierungsfaktor der betroffenen Achse größer als 1

### Requirement: Kontrolle und Übernahme
Nach der Berechnung SHALL das Programm die Korrektur vorläufig anwenden, die Abweichung am Kontrollkreuz in Pixeln anzeigen und erst nach Bestätigung speichern. Liegt die Abweichung über einer Schwelle, SHALL es darauf hinweisen und eine Wiederholung anbieten.

#### Scenario: Kleine Abweichung
- **WHEN** das Kontrollkreuz mit geringer Abweichung getroffen wird
- **THEN** zeigt das Programm die Abweichung an und bietet Speichern und Wiederholen an

#### Scenario: Große Abweichung
- **WHEN** die Abweichung am Kontrollkreuz über der Schwelle liegt
- **THEN** weist das Programm auf eine wahrscheinliche Fehlberührung hin und empfiehlt Wiederholen

### Requirement: Dauerhafte Speicherung
Beim Speichern SHALL das Programm Ausrichtung und Korrektur in die Kivy-Konfiguration des Benutzers schreiben, vorher eine Sicherungskopie der bisherigen Datei anlegen und alle anderen Einträge unverändert lassen. Die gespeicherten Werte SHALL für jede danach gestartete Kivy-App des Benutzers gelten.

#### Scenario: Sicherung vor dem Schreiben
- **WHEN** eine Kalibrierung gespeichert wird
- **THEN** existiert danach eine Sicherungskopie mit dem vorherigen Inhalt der Konfiguration

#### Scenario: Wirkung auf die Tisch-App
- **WHEN** nach dem Speichern `touch-demo/app.py` gestartet wird
- **THEN** liegt eine Karte unter dem Finger, der sie berührt

### Requirement: Neustart in den Touchtest
Nach dem Speichern SHALL das Programm sich selbst neu starten und direkt den Touchtest öffnen, damit die gespeicherte Kalibrierung sofort über den normalen Eingabeweg geprüft werden kann.

#### Scenario: Nach dem Speichern
- **WHEN** die Kalibrierung gespeichert wurde
- **THEN** startet das Programm neu und zeigt den Touchtest statt des Menüs

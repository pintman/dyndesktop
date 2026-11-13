# Spec Delta

## Purpose

Legt fest, welche Inhalte als Karten erscheinen, wie sie aus einem Inhaltsordner entstehen und wie weitere Kartentypen hinzukommen.

## ADDED Requirements

### Requirement: Inhaltsordner
Die Tisch-App SHALL ihre Karten aus einem Inhaltsordner laden, der beim Start angegeben werden kann. Ohne Angabe SHALL sie den Ordner `inhalte/` im Projektverzeichnis verwenden. Je unterstützter Datei SHALL genau eine Karte entstehen. Unterordner und nicht unterstützte Dateien SHALL sie ignorieren.

#### Scenario: Ordner angegeben
- **WHEN** die App mit einem anderen Inhaltsordner gestartet wird
- **THEN** zeigt sie genau die unterstützten Dateien dieses Ordners als Karten

#### Scenario: Nicht unterstützte Datei
- **WHEN** im Inhaltsordner eine Datei mit unbekannter Endung liegt
- **THEN** entsteht dafür keine Karte und die App startet normal

#### Scenario: Ordner fehlt oder ist leer
- **WHEN** der Inhaltsordner nicht existiert oder keine unterstützte Datei enthält
- **THEN** startet die App mit leerer Fläche und zeigt einen Hinweis mit dem Ordnerpfad

### Requirement: Textkarte
Eine Datei mit Endung `.txt` SHALL als Textkarte erscheinen, die den Dateiinhalt als UTF-8 mit Zeilenumbruch an der Kartenbreite anzeigt.

#### Scenario: Text mit Umlauten
- **WHEN** eine `.txt`-Datei mit Umlauten und mehreren Absätzen geladen wird
- **THEN** zeigt die Textkarte den Text mit Umlauten und Absätzen korrekt umbrochen an

### Requirement: Bildkarte
Dateien mit Endung `.jpg`, `.jpeg` oder `.png` SHALL als Bildkarte erscheinen. Die Karte SHALL das Seitenverhältnis des Bildes haben.

#### Scenario: Hochformat
- **WHEN** ein Bild im Hochformat geladen wird
- **THEN** ist die Bildkarte höher als breit und das Bild füllt sie ohne Verzerrung

### Requirement: Videokarte
Dateien mit Endung `.mp4` oder `.webm` SHALL als Videokarte erscheinen, die das Video stumm in Endlosschleife abspielt. Die Karte SHALL das Seitenverhältnis des Videos haben.

#### Scenario: Video läuft
- **WHEN** eine Videodatei geladen wird
- **THEN** spielt die Videokarte das Video ohne Ton ab und beginnt nach dem Ende von vorn

#### Scenario: Video bewegen
- **WHEN** eine laufende Videokarte verschoben, gedreht oder skaliert wird
- **THEN** läuft das Video ohne Unterbrechung weiter

### Requirement: Unlesbare Datei
Lässt sich eine unterstützte Datei nicht lesen oder abspielen, SHALL statt des Inhalts eine Karte mit Dateiname und Fehlerhinweis erscheinen. Die übrigen Karten SHALL davon nicht betroffen sein.

#### Scenario: Defektes Video
- **WHEN** eine `.mp4`-Datei geladen wird, die kein gültiges Video enthält
- **THEN** zeigt die Karte den Dateinamen und einen Fehlerhinweis, und alle anderen Karten werden normal angezeigt

### Requirement: Erweiterbare Kartentypen
Ein neuer Kartentyp SHALL sich hinzufügen lassen, indem er einmal mit seinen Dateiendungen angemeldet wird, ohne Tischfläche, Gesten, Bearbeitung oder bestehende Kartentypen zu ändern. Ein angemeldeter Typ SHALL dieselben Gesten und dasselbe Nachrutschen wie alle Karten erhalten.

#### Scenario: Neuer Typ für neue Endung
- **WHEN** ein Kartentyp für eine bisher unbekannte Endung angemeldet ist und eine solche Datei im Inhaltsordner liegt
- **THEN** erscheint für sie eine Karte dieses Typs, die sich wie jede andere Karte bewegen lässt

#### Scenario: Doppelte Endung
- **WHEN** ein Kartentyp für eine Endung angemeldet wird, die bereits einem anderen Typ gehört
- **THEN** wird die Anmeldung mit einer Fehlermeldung abgelehnt

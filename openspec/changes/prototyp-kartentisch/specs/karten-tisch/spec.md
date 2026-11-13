# Spec Delta

## Purpose

Stellt die Tischfläche bereit, auf der Karten liegen und von mehreren Personen gleichzeitig per Touch bewegt, gedreht und skaliert werden.

## ADDED Requirements

### Requirement: Karten auf der Fläche
Die Tisch-App SHALL beim Start alle geladenen Karten auf der Fläche anzeigen, ohne dass Karten vollständig außerhalb des sichtbaren Bereichs liegen. Sie SHALL im Fenster laufen, solange kein Vollbild von außen konfiguriert ist.

#### Scenario: Start mit Beispielinhalten
- **WHEN** die App mit dem Beispiel-Inhaltsordner gestartet wird
- **THEN** sind Textkarte, Bildkarten und Videokarte sichtbar und jede liegt zumindest teilweise im Fenster

#### Scenario: Vollbild von außen
- **WHEN** die App mit konfiguriertem Vollbild (z. B. `KCFG_GRAPHICS_FULLSCREEN=auto`) startet
- **THEN** füllt sie den Bildschirm, ohne dass die App selbst geändert wurde

### Requirement: Verschieben
Eine Karte SHALL einem Finger folgen, der auf ihr aufsetzt und sich bewegt. Die berührte Karte SHALL dabei über allen anderen Karten liegen.

#### Scenario: Karte ziehen
- **WHEN** ein Finger auf einer Karte aufsetzt und über die Fläche gezogen wird
- **THEN** bleibt die Karte unter dem Finger und liegt über den anderen Karten

#### Scenario: Überlappende Karten
- **WHEN** zwei Karten sich überlappen und ein Finger auf die Überlappung tippt
- **THEN** reagiert nur die oben liegende Karte

### Requirement: Drehen und Skalieren
Mit zwei Fingern auf derselben Karte SHALL sich die Karte drehen und skalieren lassen. Die Skalierung SHALL auf das 0,3- bis 4-Fache der Ausgangsgröße begrenzt sein.

#### Scenario: Zwei-Finger-Geste
- **WHEN** zwei Finger auf einer Karte auseinander gezogen und dabei gedreht werden
- **THEN** wird die Karte größer und dreht sich mit den Fingern

#### Scenario: Grenze der Skalierung
- **WHEN** eine Karte über das 4-Fache hinaus vergrößert werden soll
- **THEN** bleibt sie beim 4-Fachen ihrer Ausgangsgröße

### Requirement: Gleichzeitige Bedienung
Mehrere Karten SHALL sich unabhängig voneinander gleichzeitig von verschiedenen Fingern bewegen lassen.

#### Scenario: Zwei Personen
- **WHEN** zwei Finger gleichzeitig je eine andere Karte ziehen
- **THEN** bewegen sich beide Karten unabhängig voneinander

### Requirement: Nachrutschen
Wird eine Karte nach dem Ziehen mit einem Finger in Bewegung losgelassen, SHALL sie in Bewegungsrichtung weiterrutschen und durch Reibung bis zum Stillstand abbremsen. Nach einer Zwei-Finger-Geste SHALL sie nicht nachrutschen.

#### Scenario: Wischen und loslassen
- **WHEN** eine Karte mit einem Finger schnell gezogen und in der Bewegung losgelassen wird
- **THEN** rutscht sie weiter und kommt nach kurzer Strecke zum Stehen

#### Scenario: Langsam abgelegt
- **WHEN** eine Karte ohne Bewegung losgelassen wird
- **THEN** bleibt sie an dieser Stelle liegen

#### Scenario: Nach Drehen
- **WHEN** eine Karte mit zwei Fingern gedreht und dann losgelassen wird
- **THEN** bleibt sie ohne Nachrutschen liegen

#### Scenario: Rutschende Karte fangen
- **WHEN** ein Finger auf eine noch rutschende Karte tippt
- **THEN** hält die Karte sofort an

### Requirement: Begrenzung auf die Fläche
Eine rutschende Karte SHALL anhalten, wenn ihr Mittelpunkt den Rand der Fläche erreicht.

#### Scenario: Wurf zum Rand
- **WHEN** eine Karte kräftig Richtung Rand gewischt wird
- **THEN** hält sie an, sobald ihr Mittelpunkt den Rand erreicht, und bleibt erreichbar

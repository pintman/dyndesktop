# Spec Delta

## Purpose

Ermöglicht, Karteninhalte direkt am Tisch per Touch zu bearbeiten: Bearbeitung per langem Touch öffnen, mit einer beweglichen virtuellen Tastatur eingeben, übernehmen oder verwerfen.

## ADDED Requirements

### Requirement: Bearbeitung per langem Touch
Bleibt ein einzelner Finger mindestens 0,8 s nahezu ruhig (höchstens 10 px Bewegung) auf einer Karte, SHALL die Bearbeitung dieser Karte öffnen. Bewegt sich der Finger weiter oder kommt ein zweiter Finger auf dieselbe Karte, SHALL keine Bearbeitung öffnen.

#### Scenario: Langer Touch
- **WHEN** ein Finger 0,8 s ruhig auf einer Textkarte liegt
- **THEN** öffnet die Bearbeitung der Textkarte und die virtuelle Tastatur erscheint

#### Scenario: Ziehen statt Halten
- **WHEN** ein Finger auf einer Karte aufsetzt und sie innerhalb von 0,8 s verschiebt
- **THEN** wird die Karte nur verschoben, eine Bearbeitung öffnet nicht

#### Scenario: Zwei Finger
- **WHEN** zwei Finger ruhig auf einer Karte liegen
- **THEN** öffnet keine Bearbeitung

### Requirement: Bearbeitungsansicht
Während der Bearbeitung SHALL die Karte ein Eingabefeld mit dem aktuellen Wert sowie die Elemente Übernehmen und Abbrechen zeigen. Abbrechen SHALL die Bearbeitung ohne Änderung schließen.

#### Scenario: Abbrechen
- **WHEN** in der Bearbeitung Text geändert und dann Abbrechen berührt wird
- **THEN** zeigt die Karte wieder den vorherigen Inhalt, Tastatur und Eingabefeld verschwinden, die Datei ist unverändert

### Requirement: Eine Bearbeitung gleichzeitig
Es SHALL höchstens eine Bearbeitung zur selben Zeit offen sein. Ein langer Touch auf eine andere Karte während einer offenen Bearbeitung SHALL keine zweite Bearbeitung öffnen und kurz darauf hinweisen.

#### Scenario: Zweite Karte
- **WHEN** eine Bearbeitung offen ist und ein Finger lange auf eine andere Karte drückt
- **THEN** bleibt die erste Bearbeitung offen, und an der anderen Karte erscheint kurz ein Hinweis

### Requirement: Textinhalt ändern
In der Bearbeitung einer Textkarte SHALL das Eingabefeld den vollständigen Text mit Zeilenumbrüchen enthalten. Übernehmen SHALL den neuen Text auf der Karte anzeigen und ihn als UTF-8 in die zugehörige Datei schreiben. Schlägt das Schreiben fehl, SHALL die Bearbeitung mit Fehlerhinweis offen bleiben.

#### Scenario: Text übernehmen
- **WHEN** der Text einer Textkarte geändert und Übernehmen berührt wird
- **THEN** zeigt die Karte den neuen Text, und die `.txt`-Datei enthält ihn

#### Scenario: Neustart nach Änderung
- **WHEN** nach einer übernommenen Textänderung die App neu gestartet wird
- **THEN** zeigt die Textkarte den geänderten Text

#### Scenario: Datei schreibgeschützt
- **WHEN** die `.txt`-Datei nicht beschreibbar ist und Übernehmen berührt wird
- **THEN** bleibt die Bearbeitung mit dem eingegebenen Text offen und zeigt einen Fehlerhinweis

### Requirement: Dateiname ändern
In der Bearbeitung einer Bild- oder Videokarte SHALL das Eingabefeld den Dateinamen ohne Pfad enthalten. Übernehmen SHALL die Karte auf die genannte Datei im Inhaltsordner umstellen. Dateien auf der Platte SHALL dabei nicht umbenannt oder verändert werden.

#### Scenario: Anderes Bild
- **WHEN** in einer Bildkarte der Name eines anderen Bildes aus dem Inhaltsordner eingegeben und übernommen wird
- **THEN** zeigt die Karte dieses Bild mit dessen Seitenverhältnis, und keine Datei wurde umbenannt

#### Scenario: Anderes Video
- **WHEN** in einer Videokarte der Name eines anderen Videos aus dem Inhaltsordner übernommen wird
- **THEN** spielt die Karte das neue Video ab

### Requirement: Ungültiger Dateiname
Übernehmen SHALL abgelehnt werden, wenn der eingegebene Name keine Datei im Inhaltsordner bezeichnet, einen Pfad enthält oder zu einem anderen Kartentyp gehört. Die Bearbeitung SHALL dann mit einem Hinweis offen bleiben, und die Karte SHALL ihren bisherigen Inhalt behalten.

#### Scenario: Datei fehlt
- **WHEN** ein Name eingegeben wird, zu dem keine Datei im Inhaltsordner existiert
- **THEN** bleibt die Bearbeitung offen mit dem Hinweis, dass die Datei fehlt

#### Scenario: Pfad im Namen
- **WHEN** ein Name mit Pfadanteil wie `../geheim.png` eingegeben wird
- **THEN** wird er abgelehnt, und es wird keine Datei außerhalb des Inhaltsordners geöffnet

#### Scenario: Falscher Typ
- **WHEN** in einer Bildkarte der Name einer Videodatei eingegeben wird
- **THEN** wird er mit Hinweis auf den falschen Kartentyp abgelehnt

### Requirement: Virtuelle Tastatur
Beim Öffnen der Bearbeitung SHALL eine virtuelle Tastatur mit deutscher Belegung einschließlich Umlauten und ß erscheinen, die in das Eingabefeld schreibt. Sie SHALL neben der Karte und in derselben Drehung wie die Karte erscheinen und beim Schließen der Bearbeitung verschwinden.

#### Scenario: Tippen
- **WHEN** auf der virtuellen Tastatur „Größe“ getippt wird
- **THEN** steht „Größe“ im Eingabefeld

#### Scenario: Gedrehte Karte
- **WHEN** die Bearbeitung einer um 180° gedrehten Karte geöffnet wird
- **THEN** erscheint die Tastatur ebenfalls um 180° gedreht neben der Karte

#### Scenario: Andere Karte bewegen
- **WHEN** während einer offenen Bearbeitung eine andere Karte verschoben wird
- **THEN** bleiben Bearbeitung und Tastatur offen

### Requirement: Bewegliche Tastatur
Die virtuelle Tastatur SHALL sich mit denselben Gesten wie eine Karte verschieben, drehen und skalieren lassen, ohne dass dabei Tasten ausgelöst werden. Sie SHALL nach dem Loslassen nicht nachrutschen.

#### Scenario: Tastatur verschieben
- **WHEN** die Tastatur an ihrem Rand mit einem Finger gezogen wird
- **THEN** folgt sie dem Finger, und es wird kein Zeichen eingegeben

#### Scenario: Tastatur drehen und skalieren
- **WHEN** die Tastatur mit zwei Fingern gedreht und vergrößert wird
- **THEN** dreht und vergrößert sie sich, und die Tasten bleiben bedienbar

### Requirement: Physische Tastatur
Ist eine physische Tastatur angeschlossen, SHALL sie während einer offenen Bearbeitung zusätzlich in das Eingabefeld schreiben.

#### Scenario: Entwicklung am Mac
- **WHEN** am Mac eine Bearbeitung offen ist und auf der eingebauten Tastatur getippt wird
- **THEN** erscheinen die Zeichen im Eingabefeld

# Design

## Context

- `touch-demo/app.py` enthält `SchwungKarte` (Scatter + zwei `KineticEffect`, Reibung 0,05, Stopp am Fensterrand, kein Schwung nach Mehrfinger-Geste) und `kartengroesse` (Seitenverhältnis, längste Seite 400 px). Beides ist erprobt und wird übernommen.
- Kivy 2.3 (Poetry-venv, Python 3.13). Kivy bringt `VKeyboard` mit. Diese Klasse ist selbst ein `Scatter`. Im freien Modus (`docked=False`) setzt sie `do_translation/do_rotation/do_scale = True`. Berührungen im Rand (`margin_hint`) verschieben die Tastatur, Berührungen auf Tasten lösen Tasten aus. Das Layout `qwertz.json` enthält ä, ö, ü und ß.
- `Window.request_keyboard` legt im Modus `multi`/`systemandmulti` eine Tastatur pro Ziel-Widget an und hängt sie an das Window. Mit `Window.set_vkeyboard_class` lässt sich eine eigene Klasse setzen.
- Video braucht in Kivy einen Provider. Im Projekt ist keiner installiert (weder ffpyplayer noch GStreamer).
- Zusammenspiel mit `inbetriebnahme-touchrahmen`: siehe proposal.md, Abschnitt Verträglichkeit.

## Goals / Non-Goals

**Goals:**
- Reine Logik (Kartenregistry, Laden des Ordners, Prüfung des Dateinamens, Speichern von Text, Erkennung des langen Touchs) ohne Kivy-Fenster mit pytest testbar.
- Am Mac per Maus bedienbar (Rechtsklick = zweiter Finger) und auf dem Tisch per Touch, ohne Codeänderung.

**Non-Goals:**
- Mehrere Bearbeitungen gleichzeitig, mehrere Tastaturen.
- Ton bei Videos, Wiedergabesteuerung (Pause, Spulen).
- Beobachten des Inhaltsordners zur Laufzeit (neue Dateien erscheinen erst nach Neustart).
- Grenzen für die Tastatur auf der Fläche, Nachrutschen der Tastatur.

## Decisions

### D1: Paketaufbau
```
tisch/
  __main__.py      Argumente (--inhalte), Kivy-Config im Speicher setzen, App starten
  app.py           TischApp: Fläche, Karten platzieren, Hinweis bei leerem Ordner
  karte.py         SchwungKarte (aus touch-demo) + Langdruck-Anbindung
  langdruck.py     reine Zustandsmaschine: down/move/up/zweiter Finger + Zeit → ausgelöst?
  typen/
    __init__.py    Registry: registriere(typ), typ_fuer(pfad), Fehler bei doppelter Endung
    basis.py       Kartentyp-Basisklasse
    text.py        TextTyp
    bild.py        BildTyp
    video.py       VideoTyp
  inhalte.py       nur Standardbibliothek: Ordner scannen, Dateinamen prüfen, Text atomar schreiben
  bearbeitung.py   Bearbeitungsansicht, Tastatur öffnen/platzieren/schließen, „eine gleichzeitig“
  tastatur.py      TischTastatur(VKeyboard): Layout qwertz, ohne Andocken
inhalte/           Beispielinhalte
tests/             pytest für langdruck, typen-Registry, inhalte
```
- *Alternative:* `touch-demo/app.py` erweitern. Verworfen (Entscheidung des Nutzers). `touch-demo` bleibt die minimale Referenz.

### D2: Kartentyp-Schnittstelle und Registry
```python
class Kartentyp:
    name: str                  # "text", "bild", "video"
    endungen: tuple[str, ...]  # (".txt",)
    def erzeuge_inhalt(self, pfad) -> Widget        # darf werfen → Fehlerkarte
    def groesse(self, inhalt) -> (w, h)             # Seitenverhältnis
    def bearbeitungswert(self, pfad, inhalt) -> str  # Text bzw. Dateiname
    def uebernehme(self, karte, wert) -> None        # wirft BearbeitungsFehler mit Hinweistext
```
- Die Registry ordnet Endungen (klein geschrieben) Typen zu. Eine doppelte Endung löst `ValueError` aus. Die eingebauten Typen melden sich beim Import von `tisch.typen` an.
- Die Karte (`SchwungKarte`) kennt nur `Kartentyp`. Gesten, Schwung und Langdruck gelten so automatisch für jeden Typ (Spec kartentypen „Erweiterbare Kartentypen“).
- Bild- und Videotyp teilen eine Hilfsfunktion für „Dateiname wechseln“. `uebernehme` prüft den Namen mit `inhalte.pruefe_dateiname(ordner, name, typ)` und tauscht dann `source`. Die Kartengröße wird bei neuem `texture_size` an das neue Seitenverhältnis angepasst. Mittelpunkt, Drehung und Skalierung bleiben erhalten.
- *Alternative:* Entry Points (Plugins über `pyproject`). Für den POC zu schwer. Mit der Registry geht das später trotzdem.

### D3: Prüfen des Dateinamens
`pruefe_dateiname` lehnt ab:
- Namen mit `/`, `\`, `..` oder einen absoluten Pfad
- Namen, deren `Path(ordner, name).resolve()` nicht direkt in `ordner.resolve()` liegt (das deckt Symlinks ab)
- nicht existierende Dateien
- Endungen, die nicht zum Typ der Karte gehören

Jeder Fall hat einen eigenen Hinweistext. Rein in der Standardbibliothek, mit `tmp_path` testbar.

### D4: Text speichern
`schreibe_text(pfad, text)`: Zuerst wird `os.access(pfad, W_OK)` geprüft. Danach wird in eine temporäre Datei im selben Ordner geschrieben und mit `os.replace` getauscht. Kodierung UTF-8, Zeilenenden `\n`.
- *Warum die Prüfung:* `os.replace` ersetzt unter POSIX auch schreibgeschützte Dateien, wenn der Ordner beschreibbar ist. Ohne die Prüfung würde das Szenario „Datei schreibgeschützt“ fehlschlagen.

### D5: Langer Touch
- `langdruck.Erkenner` ist eine reine Klasse mit `down(uid, pos, t)`, `move(uid, pos)`, `up(uid)` und `faellig(t) -> bool`. Schwellen: 0,8 s, 10 px. Ein zweiter aktiver Touch bricht ab.
- `SchwungKarte.on_touch_down` startet den Erkenner und `Clock.schedule_once(…, 0.8)`. Bei Auslösung wird der Schwung gestoppt und der Touch per `ungrab` freigegeben. Danach öffnet `bearbeitung.oeffne(karte)`.
- Die Schwelle in px wird mit `kivy.metrics.dp` umgerechnet, damit sie am Mac (Retina) und am Tisch gleich wirkt.
- *Alternative:* Kivys `touch.is_double_tap`/eigene Gestenerkennung. Verworfen: Ein Doppeltipp kollidiert mit Fangen + Ziehen, und Kivy hat keinen eingebauten Langdruck.

### D6: Virtuelle Tastatur über Kivy-Mechanismus
- `__main__` setzt vor dem Import von `kivy.core.window` im Speicher `Config.set('kivy', 'keyboard_mode', 'systemandmulti')` und `keyboard_layout = 'qwertz'`. In `config.ini` wird nichts geschrieben. Die Konfiguration aus `inbetriebnahme` bleibt dadurch unberührt.
- `Window.set_vkeyboard_class(TischTastatur)`. `TischTastatur` setzt eine sinnvolle Startgröße (z. B. 700×260 px) und bleibt frei, also nicht angedockt.
- Das Eingabefeld (`TextInput`) der Bearbeitung hat `unfocus_on_touch=False`. Berührungen anderer Karten schließen die Tastatur deshalb nicht. Geschlossen wird nur über Übernehmen/Abbrechen (`focus = False` → `release_keyboard` entfernt die Tastatur).
- Platzierung: Nach `focus = True` holt `bearbeitung` die Tastatur über `textinput._keyboard.widget`. Ist das nicht verfügbar, sucht sie in `Window.children` nach einer `TischTastatur`. Dann setzt sie `rotation = karte.rotation` und legt sie in Kartenkoordinaten unter die Karte (`karte.to_parent`). Ein Teil des Fensters bleibt dabei immer sichtbar.
- Textkarte: `multiline=True`, Enter erzeugt einen Zeilenumbruch. Bild/Video: `multiline=False`, Enter = Übernehmen.
- *Alternative:* `VKeyboard` selbst erzeugen und `on_textinput` an das Feld weiterreichen. Bleibt Ausweichweg, falls die Platzierung über `_keyboard` nicht zuverlässig ist. Die Spec ist davon nicht betroffen.

### D7: Bearbeitungsansicht
- Die Bearbeitung legt ein Overlay als Kind **in** den Scatter der Karte: Eingabefeld über dem Inhalt sowie Knöpfe Übernehmen und Abbrechen am unteren Rand. Das Overlay dreht und skaliert mit der Karte.
- Ein modulweiter Zustand `aktive_bearbeitung` sorgt für „eine gleichzeitig“. Bei einem zweiten Langdruck erscheint ein kurzer Hinweis (Label, 1,5 s) auf der anderen Karte.
- Fehler aus `uebernehme` (`BearbeitungsFehler`) erscheinen als rote Zeile im Overlay. Die Bearbeitung bleibt offen.

### D8: Video
- `kivy.uix.video.Video(source, state='play', volume=0, options={'eos': 'loop'})`. Provider ist `ffpyplayer` als Abhängigkeit in `pyproject.toml`. Wheels gibt es für macOS und Linux x86_64.
- Seitenverhältnis: Bis `texture` geladen ist, gilt 16:9. Bei `on_texture` wird die Kartengröße mit `kartengroesse` angepasst.
- Fehler: Ein defektes Video wirft beim Erzeugen nicht zwingend. Darum werden `on_eos`/`loaded` ausgewertet, ebenso eine Prüfung nach 3 s ohne Textur. Danach tauscht die Karte den Inhalt gegen eine Fehleranzeige.
- *Alternative:* GStreamer. Verworfen: Unter macOS schwer zu installieren, unter Debian zusätzliche Systempakete.

### D9: Anordnung beim Start
Die Karten werden in einem Raster nach Dateiname sortiert verteilt, mit leichter Zufallsdrehung (±8°, fester Seed). Gibt es mehr Karten, als ins Raster passen, liegen sie leicht versetzt übereinander, aber immer innerhalb des Fensters.

### D10: Fehlerkarte und leerer Ordner
- Wirft `erzeuge_inhalt`, entsteht eine graue Karte mit Dateiname und Fehlermeldung. Sie bleibt beweglich, aber ohne Bearbeitung.
- Bei leerem oder fehlendem Ordner erscheint ein Label in der Mitte: „Keine Inhalte in <pfad>“.

## Risks / Trade-offs

- [Rahmen liefert nur Single-Touch] → Drehen und Skalieren sind dann am Tisch nicht nutzbar. Das ist bewusst hingenommen (Entscheidung), Klärung über den Touchtest aus `inbetriebnahme-touchrahmen`.
- [IR-Rahmen meldet Geistertouches oder zitternde Positionen] → Ein Geistertouch kann einen Langdruck auslösen, Zittern kann ihn verhindern. Abhilfe: Die Schwellen 0,8 s / 10 dp sind Konstanten, die nach dem Touchtest am Gerät angepasst werden.
- [Platzierung der Tastatur greift auf das Kivy-Interna `_keyboard` zu] → Als Ausweichweg dient die Suche in `Window.children`. Danach bleibt die eigene `VKeyboard` (D6, Alternative).
- [VKeyboard im Modus `multi` reagiert unter cage/SDL2 anders als am Mac] → In der Abnahme am Gerät prüfen. Die physische Tastatur wirkt dank `systemandmulti` zusätzlich.
- [ffpyplayer-Wheel für Python 3.13 fehlt auf einer Plattform] → Beim Installieren sofort sichtbar. Ausweichweg: GStreamer-Provider aus den Debian-Paketen (`python3-gst-1.0`) bzw. Python 3.12.
- [Video im Repo: ca. 4 MB] → Für den POC hingenommen. Später gehören Inhalte nicht ins Repo.
- [`setup.sh` aus `inbetriebnahme` installiert nur kivy] → Anpassung in jenem Change (proposal.md). Bis dahin installiert man `ffpyplayer` auf dem Tisch von Hand.
- [Textkarte mit sehr langem Text] → Die Karte zeigt nur den Anfang, der Rest wird abgeschnitten. In der Bearbeitung ist das Feld scrollbar.

## Migration Plan

Neue Dateien, keine Migration. Damit der Kiosk die neue App startet, muss `inbetriebnahme-touchrahmen` angepasst werden (proposal.md, Punkte 1–3). Am besten geschieht das per `/opsx:update` an jenem Change, bevor er umgesetzt wird.

## Open Questions

- Startgröße der Tastatur auf dem 40"-Tisch: Sie lässt sich nach der Abnahme am Gerät festlegen und ist eine reine Konstante.

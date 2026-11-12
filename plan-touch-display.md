# folk-carthag – Digitaler Touch-Tisch

Recherche und Konzept für einen selbstgebauten Multitouch-Tisch, der Dateien anzeigt, Textbearbeitung erlaubt und Drag & Drop von Inhalten unterstützt.

---

## 1. Ausgangslage: Touch unter Linux

Interaktive Displays (z. B. **Prowise Touchscreen**) und günstige **IR-Touchrahmen** melden Touch per USB als Standard-**USB-HID-Multitouch**-Gerät. Linux unterstützt das ohne Treiber (`hid-multitouch` + `libinput`).

**Checkliste**

- Touch-USB-Kabel (meist Typ B) zusätzlich zu HDMI anschließen. Es muss der Touch-Port sein, der zum gewählten HDMI-Eingang gehört.
- Erkennung prüfen:
  ```bash
  lsusb
  sudo libinput list-devices | grep -i -A5 touch
  sudo evtest            # Gerät wählen, Board antippen
  sudo libinput debug-events   # wie viele Touchpunkte kommen gleichzeitig an?
  dmesg | tail           # direkt nach dem Einstecken
  ```
- Touch dem richtigen Bildschirm zuordnen:
  - X11: `xinput map-to-output <ID> HDMI-1`
  - niri: `input { touch { map-to-output "HDMI-A-1" } }`
  - allgemein: udev-Regel mit `LIBINPUT_CALIBRATION_MATRIX`
- Wird das Gerät nicht erkannt: VID:PID manuell an `hid-multitouch` übergeben (siehe Arch-Wiki).
- Prowise-Software: Presenter läuft im Browser. Native Tools (Screen Share, Updater) gibt es nur für Windows/macOS.

---

## 2. Vorbild: Grant Custers Tabletop-Computer

Quelle: [My tabletop computer setup](https://feed.grantcuster.com/post/2026-11-03-10-51-03-my-tabletop-computer-setup) (Nov. 2026)

**Hardware**

- Hisense-Fernseher 55" als Display
- IR-Touchrahmen 43", in den TV-Rahmen eingelassen. Bündige Oberfläche, günstiger als kapazitiv, erkennt aber schon knapp über der Fläche.
- entspiegelnde Schutzfolie 50" und Plexiglas (1/8") als oberste Schicht
- Mini-PC, Unterkonstruktion aus Sperrholz

**Software**

- Linux (Distribution nicht genannt)
- [niri](https://github.com/niri-wm/niri) (Wayland-Compositor), um Bild und Touch nur auf den vom Rahmen abgedeckten Teilbereich zu legen
- kein spezieller Touch-Treiber (Plug-and-Play)
- Demos: <https://tabletop.grantcuster.com>

**Repos** ([github.com/GrantCuster](https://github.com/GrantCuster))

| Repo | Inhalt |
|---|---|
| [tabletop-demos](https://github.com/GrantCuster/tabletop-demos) | statische Demo-Galerie (Videos aus Bluesky-Posts), Vite + TypeScript |
| [tabletop](https://github.com/GrantCuster/tabletop) | Webcam-Bilder anzeigen/zuschneiden, React + TypeScript + Vite |
| [feed-grantcuster-com](https://github.com/GrantCuster/feed-grantcuster-com) | Code seines Feeds/Blogs |

Ein Repo mit niri-Konfiguration oder Dotfiles wurde nicht gefunden.

---

## 3. Anforderungen

- Dateien anzeigen (Bilder, Video, PDF, Text)
- Text bearbeiten und speichern
- Inhalte per Drag & Drop frei verschieben, drehen, skalieren
- mehrere Personen gleichzeitig, von allen Tischseiten

---

## 4. Hardware-Optionen

| Option | Vorteile | Nachteile |
|---|---|---|
| TV + IR-Touchrahmen + Glas/Plexi | günstig, groß | Rahmen bündig einlassen, Touch reagiert knapp über der Fläche |
| vorhandenes Prowise-Board liegend | Touch und Bild fertig | Gewicht, Lüftung, Garantie bei liegendem Betrieb klären |

**Rechner:** Mini-PC mit Intel N100/N150 reicht für Web-Apps. Für 3D lieber Ryzen mit stärkerer iGPU.

### Gewählter Touchrahmen: LMENGER LM-40IN

Quelle: [Amazon B0FDG54QFM](https://www.amazon.de/dp/B0FDG54QFM) (Stand 12.11.2026)

| Merkmal | Wert |
|---|---|
| Größe | 40", 16:9 (auch 32/50/55/65" erhältlich) |
| Preis | 160,99 € (32": 150,99 €, 55": 200,99 €, 65": 210,99 €) |
| Touchpunkte | 20 gleichzeitig |
| Anschluss | USB, 5 V über USB, „treiberfrei“ |
| Reaktionszeit | 20 ms |
| Abmessungen | ca. 107 × 7,2 × 5 cm (laut Datenblatt, Angabe unklar) |
| Bauform | Alurahmen, wird außen auf den Bildschirm geklebt; ohne Glas, ohne Display |
| Montage | Steckverbinder A-A … D-D, Montagehilfen + Schraubendreher dabei |
| Bewertung | 4,6/5 (11 Bewertungen) |

**Risiken**

- **Linux-Multitouch unklar.** Die Angaben widersprechen sich: Aufzählung nennt „Linux ab Kernel 3.5“, die Produktinfo sagt „Linux/Ubuntu: Single-Touch; Multitouch erfordert kundenspezifische Entwicklung“. Viele dieser Rahmen melden sich trotzdem als HID-Multitouch. → Direkt nach Lieferung mit `libinput debug-events` prüfen (Abschnitt 1), innerhalb der Rückgabefrist.
- **Aufliegend statt bündig.** Der Rahmen klebt auf dem Bildschirm, ist also nicht für den bündigen Einbau wie bei Grant Custer gedacht. Für den Tisch Rahmen in die Unterkonstruktion einlassen oder eigene Halterung bauen. Eine Rezension (55") berichtet, dass das Klebeband nicht hält.
- **Größe passend zum Display.** Der Rahmen muss zur Bilddiagonale des Fernsehers passen (40"-TV oder, wie bei Grant Custer, größerer TV und Bild per niri auf die Rahmenfläche begrenzen).
- Glas/Plexi als Schutzschicht muss innerhalb des Rahmens liegen, damit die IR-Strahlen knapp über der Fläche bleiben.

---

## 5. Software-Varianten

**Grundsatzentscheidung:** Linux ohne Desktop → Kiosk-Compositor (siehe Abschnitt 6) → eine eigene Vollbild-App (Variante B oder C).

**Warum kein klassischer Desktop?**
- Unter X11 funktioniert Multitouch nur schlecht → nur Wayland kommt in Frage.
- Wayland schickt jeden Touchpunkt an das Fenster unter dem Finger. Parallele Eingaben in verschiedenen Apps klappen also.
- Drag & Drop, Fenster verschieben und Tastaturfokus gibt es aber **nur einmal pro System**. Zwei Personen können nicht gleichzeitig Dateien ziehen.
- Desktops sind in eine Richtung ausgerichtet. An einem Tisch schauen Leute aber von allen Seiten drauf.
- → Eine eigene Vollbild-App, die Multitouch selbst verarbeitet, ist für einen Tisch mit mehreren Nutzern besser geeignet.

### Variante A: Standard-Desktop (Fallback für einzelne Nutzer)

- **GNOME unter Wayland**: beste Touch-Unterstützung und eingebaute Bildschirmtastatur
- **KDE Plasma 6 unter Wayland**: Touch-Modus, Randgesten, Bildschirmtastatur, Touchscreen lässt sich einem Monitor zuordnen
- Nautilus (Dateien), GNOME Text Editor, Papers/Evince (PDF), Loupe (Bilder)
- Drag & Drop zwischen Apps geht, ist aber nicht auf einen Tisch ausgelegt (s. o.)
- wirkt eher wie ein großes Tablet

### Variante B: eigene Canvas-Web-App (empfohlen)

Alle Inhalte liegen als frei bewegliche Karten auf einer Fläche.

| Ebene | Empfehlung |
|---|---|
| OS | Debian 13 oder Fedora |
| Compositor | **cage** (Kiosk, eine App im Vollbild), **Weston** oder **niri** (siehe Abschnitt 6) |
| Laufzeit | Chromium im Kiosk-Modus: `chromium --kiosk --ozone-platform=wayland --touch-events=enabled <URL>` |
| Autostart | Autologin + systemd-User-Service mit cage |
| Canvas | **Excalidraw** (MIT) oder **Konva.js**/PixiJS (selbst gebaut). Alternative **tldraw**: für Produktivbetrieb Lizenzschlüssel nötig, kostenlose Hobby-Lizenz für nicht-kommerzielle Nutzung, mit Wasserzeichen und Prüfung der Anfrage |
| Bilder/Video | native `<img>` / `<video>` |
| PDF | **pdf.js** |
| Texteditor | **CodeMirror 6** (Code/Markdown) oder **TipTap** (formatierter Text) |
| Backend | **FastAPI** (Python) oder Fastify (Node): Ordner auflisten, Dateien ausliefern, speichern. Neue Dateien erkennen mit watchdog/chokidar |
| Layout speichern | Positionen der Karten als JSON im Backend |
| Dateien auf den Tisch bringen | Netzwerkordner (SMB/Nextcloud), USB-Stick per Auto-Mount oder QR-Code zum Upload vom Handy |
| Build | Vite + TypeScript |

**Architektur**

```
┌────────────── Tisch (Mini-PC) ──────────────┐
│ cage → Chromium (Kiosk)                     │
│   └─ Canvas-App (Vite/TS)                   │
│       ├─ Karten: Bild | Video | PDF | Text  │
│       ├─ Pointer Events (Multitouch)        │
│       └─ Bildschirmtastatur (in der App)    │
│              │ HTTP/WebSocket               │
│ Backend (FastAPI)                           │
│   ├─ /files     Ordner listen/ausliefern    │
│   ├─ /save      Text speichern              │
│   ├─ /layout    Kartenpositionen (JSON)     │
│   └─ Watcher    neue Dateien → WebSocket    │
│              │                              │
│ Datenordner ← SMB / USB / Handy-Upload      │
└─────────────────────────────────────────────┘
```

### Variante C: native Kivy-App (Python)

Kivy wurde ursprünglich für Multitouch-Tische entwickelt. Jeder Finger ist ein eigenes Touch-Ereignis mit eigener ID.

Wichtige Bausteine:
- **`Scatter`**: jedes Objekt gleichzeitig verschieben, drehen und skalieren. So kann jede Person Inhalte zu sich drehen.
- `on_touch_down/move/up` und `touch.grab()` für eigene Gesten
- Fertige Widgets: `FileChooser`, `TextInput`, `Image`, `Video`, `VKeyboard` (Bildschirmtastatur)
- TUIO-Unterstützung für späteres kamerabasiertes Tracking
- Optional KivyMD für Material-Design-Widgets

Minimalbeispiel:
```python
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.core.window import Window

class Tisch(App):
    def build(self):
        Window.fullscreen = 'auto'
        root = FloatLayout()
        for i, f in enumerate(['a.jpg', 'b.jpg', 'c.jpg']):
            s = Scatter(size=(400, 300), pos=(100 + i * 450, 300),
                        do_rotation=True, do_scale=True)
            s.add_widget(Image(source=f, size=s.size))
            root.add_widget(s)
        return root

Tisch().run()
```

Start:
```bash
SDL_VIDEODRIVER=wayland cage -- python3 app.py
```

Stolperstellen:
- **Herkunft der Touch-Eingaben:** über SDL/Wayland (einfach) oder direkt von den Eingabegeräten (`hidinput`/`mtdev`). Der direkte Weg ist oft genauer bei vielen Fingern, braucht aber `sudo usermod -aG input $USER`.
- **Doppelte Ereignisse**, weil das Board zusätzlich Mausereignisse sendet → `~/.kivy/config.ini`:
  ```ini
  [input]
  mouse = mouse,disable_on_activity
  ```

Weitere native Alternative: **Qt Quick/QML** mit `MultiPointTouchArea` / `PointHandler`.

### Vergleich B vs. C

| | B: Web-App | C: Kivy |
|---|---|---|
| Dateianzeige (PDF, Video) | sehr gut (pdf.js, `<video>`) | eingeschränkt, PDF nur mit Zusatzbibliothek |
| Texteditor | CodeMirror/TipTap | `TextInput` (einfach) |
| Multitouch/Gesten | Pointer Events, selbst oder per Canvas-Bibliothek | `Scatter` fertig eingebaut |
| Entwicklung | Hot Reload vom Laptop | Python, kein Build |

---

## 6. Kiosk-Compositor

### Cage (erste Wahl)
Minimaler Wayland-Compositor auf Basis von wlroots. Startet genau eine Anwendung im Vollbild, ohne Fenster, Panel oder Desktop.

```bash
sudo apt install cage wlr-randr
cage -- python3 app.py          # oder: cage -- chromium --kiosk ...
```

| Option / Werkzeug | Zweck |
|---|---|
| `-s` | Wechsel auf andere Konsolen (TTYs) mit Strg+Alt+F-Taste erlauben (Debugging) |
| `-m extend` | Anzeige auf mehrere Monitore verteilen |
| `wlr-randr --output HDMI-A-1 --transform 180` | Bild zur Laufzeit drehen |
| systemd-Unit oder `greetd` | Autostart |

- Touch läuft über libinput und funktioniert ohne Konfiguration.
- Nachteil: wenige Optionen, kein Kalibrierwerkzeug.

### Weston (mehr Optionen)
Referenz-Compositor des Wayland-Projekts. Mit der kiosk-shell läuft jede App im Vollbild.

`~/.config/weston.ini`:
```ini
[core]
shell=kiosk-shell.so
idle-time=0

[output]
name=HDMI-A-1
transform=rotate-180

[autolaunch]
path=/usr/bin/python3 /home/USER/app.py
```

- Touch-Kalibrierung mit `weston-touch-calibrator`, wenn das Bild versetzt zur Touchfläche liegt.
- Apps lassen sich per App-ID festen Monitoren zuordnen (`app-ids=` im `[output]`-Block).
- Wechseln, wenn Cage nicht reicht, z. B. wegen Kalibrierung oder mehrerer Monitore.

### niri
Wie bei Grant Custer: wenn Bild und Touch nur auf einen Teilbereich des Displays gelegt werden sollen (`map-to-output`).

---

## 7. Stolperfallen

1. **Die HTML5-Drag-&-Drop-API funktioniert per Touch unter Linux unzuverlässig.** Verschieben mit Pointer Events selbst umsetzen (Canvas-Bibliotheken tun das bereits).
2. **Bildschirmtastatur:** Chromium bringt unter Linux keine mit.
   - mit cage/niri: **wvkbd** oder **squeekboard**
   - besser für den Tisch: Tastatur in der App (z. B. **simple-keyboard**), drehbar und frei platzierbar
   - pragmatisch: Bluetooth-Tastatur
3. **Mehrere Personen:** jede Berührung über `pointerId` getrennt verfolgen
4. **Keine feste Leserichtung:** Karten drehbar machen, Bedienelemente auf alle Seiten verteilen
5. **Browser-Gesten abschalten:** `touch-action: none`, `contextmenu` unterdrücken, Zoom des Browsers verhindern
6. **Große Bedienelemente** (mindestens 15 mm), keine Hover-Effekte
7. **IR-Rahmen:** reagiert knapp über der Fläche. Rahmen bündig einbauen, keine Gegenstände auf dem Tisch abstellen.

---

## 8. Entwicklung

- Vite-Dev-Server mit `npm run dev -- --host` auf dem Laptop starten, den Tisch-Browser auf diese Adresse zeigen lassen. Änderungen erscheinen dann sofort auf dem Tisch (Hot Reload).
- Fernzugriff auf den Tisch per SSH.
- Touch am Laptop testen: Chrome DevTools → Device Toolbar (simuliert nur Einzeltouch, für Multitouch echtes Gerät nutzen).

---

## 9. Vorgehen

- [ ] LMENGER-Rahmen: sofort nach Lieferung Linux-Multitouch testen (Rückgabefrist!)
- [ ] Prowise-Board per USB anschließen und prüfen, ob es erkannt wird (Treiber `hid-multitouch`, siehe Abschnitt 1)
- [ ] `libinput list-devices` / `libinput debug-events`: Wie viele Touchpunkte kommen gleichzeitig an?
- [ ] Cage installieren, Minimalbeispiel (Kivy oder Chromium-Kiosk) unter Cage starten
- [ ] Mit mehreren Personen gleichzeitig testen: Kommt jeder Finger einzeln an? Gibt es Verzögerungen?
- [ ] Bei Versatz oder mehreren Monitoren: zu Weston wechseln und kalibrieren
- [ ] Entscheidung Variante B oder C
- [ ] Funktionen umsetzen: Dateien anzeigen, Text bearbeiten (inkl. Bildschirmtastatur), Objekte per Drag & Drop verschieben/drehen/skalieren
- [ ] Autostart per systemd

---

## 10. Mögliche Aufteilung als Unterrichtsprojekt (FIAE/ITA)

| Team | Aufgabe |
|---|---|
| Infrastruktur | Linux, cage/Kiosk, Autostart, Touch-Zuordnung |
| Backend | FastAPI: Dateien, Speichern, Layout, Watcher/WebSocket |
| Canvas | Karten, Multitouch-Gesten (verschieben, drehen, zoomen) |
| Viewer/Editor | PDF, Bild, Video, CodeMirror/TipTap |
| Eingabe | Bildschirmtastatur in der App, drehbar |
| Hardware | Rahmen, Glas, Unterkonstruktion |

---

## Quellen

- [Arch Wiki – Multitouch displays](https://wiki.archlinux.org/title/Multitouch_Displays)
- [Grant Custer – My tabletop computer setup](https://feed.grantcuster.com/post/2026-11-03-10-51-03-my-tabletop-computer-setup)
- [Tabletop demos](https://tabletop.grantcuster.com/)
- [GrantCuster auf GitHub](https://github.com/GrantCuster)
- [niri](https://github.com/niri-wm/niri)
- [Cage](https://github.com/cage-kiosk/cage)
- [Weston](https://gitlab.freedesktop.org/wayland/weston)
- [Kivy](https://kivy.org/doc/stable/)
- [tldraw – FAQ](https://tldraw.dev/faq) · [tldraw – License key](https://tldraw.dev/sdk-features/license-key)

"""Kivy-App: Menü, Fläche (D13), Kalibrieren (D5/D6), Touchtest (D7)."""
import os
import subprocess
import sys
import time
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, InstructionGroup, Line, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import NoTransition, Screen, ScreenManager

from . import kivyconfig, niriconfig
from .bericht import RASTER, Bericht
from .kalibrierung import abweichung_px, bestimme, schwelle_px

PROJEKT = Path(__file__).resolve().parent.parent

PALETTE = [(0.95, 0.33, 0.31), (0.30, 0.69, 0.31), (0.13, 0.59, 0.95), (1.00, 0.76, 0.03),
           (0.61, 0.15, 0.69), (0.00, 0.74, 0.83), (1.00, 0.34, 0.13), (0.55, 0.76, 0.29),
           (0.91, 0.12, 0.39), (0.47, 0.56, 0.61)]

KNOPF = dict(font_size=sp(30), background_normal="", background_color=(0.22, 0.22, 0.26, 1))
LEISTE = dict(font_size=sp(20), background_normal="", background_color=(0.22, 0.22, 0.26, 1))


def neustart(modus=None):
    """Prozess mit anderem Modus ersetzen (gleiche PID, kiosk.sh merkt nichts) (D5)."""
    argv = [sys.executable, "-m", "inbetrieb"] + ([f"--{modus}"] if modus else [])
    os.chdir(PROJEKT)
    sys.stdout.flush()
    sys.stderr.flush()
    os.execv(sys.executable, argv)


def kreuz(gruppe, x, y, farbe=(1, 1, 1), groesse=dp(30)):
    gruppe.add(Color(*farbe))
    gruppe.add(Line(points=[x - groesse, y, x + groesse, y], width=dp(1.5)))
    gruppe.add(Line(points=[x, y - groesse, x, y + groesse], width=dp(1.5)))
    gruppe.add(Line(circle=(x, y, groesse * 0.5), width=dp(1.2)))


class Leiste(BoxLayout):
    """Knopfleiste oben; Berührungen hier zählen nie als Mess-Touch."""

    def __init__(self, **kw):
        super().__init__(size_hint=(1, None), height=dp(64), spacing=dp(6),
                         padding=dp(6), pos_hint={"top": 1}, **kw)

    def knopf(self, text, aktion, **kw):
        b = Button(text=text, **(LEISTE | kw))
        b.bind(on_release=lambda *_: aktion())
        self.add_widget(b)
        return b


# --- Menü -----------------------------------------------------------------

class MenueScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name="menue", **kw)
        box = BoxLayout(orientation="vertical", padding=dp(40), spacing=dp(20))
        box.add_widget(Label(text="Inbetriebnahme Touch-Tisch", font_size=sp(40),
                             size_hint_y=0.6))
        self.hinweis = Label(text="", font_size=sp(20), color=(1, 0.8, 0.3, 1),
                             size_hint_y=0.5, halign="center")
        self.hinweis.bind(size=lambda l, s: setattr(l, "text_size", (s[0], None)))
        box.add_widget(self.hinweis)
        app = App.get_running_app
        for text, aktion in (("Fläche", lambda: app().zeige("flaeche")),
                             ("Kalibrieren", lambda: neustart("kalibrieren")),
                             ("Touchtest", lambda: app().zeige("touchtest")),
                             ("Beenden", lambda: app().beenden())):
            b = Button(text=text, **KNOPF)
            b.bind(on_release=lambda _b, a=aktion: a())
            box.add_widget(b)
        self.add_widget(box)

    def on_pre_enter(self, *_):
        app = App.get_running_app()
        zeilen = list(app.meldungen)
        if app.flaeche_geaendert:
            zeilen.insert(0, "Fläche geändert – bitte neu kalibrieren.")
        self.hinweis.text = "\n".join(zeilen)


# --- Fläche (D13) ---------------------------------------------------------

KANTEN_DE = {"left": "links", "right": "rechts", "top": "oben", "bottom": "unten"}
# Pfeiltaste → Änderung des struts je Kante (+ = Kante wandert nach innen)
TASTEN = {"left": {275: 1, 276: -1}, "right": {276: 1, 275: -1},
          "top": {274: 1, 273: -1}, "bottom": {273: 1, 274: -1}}


class FlaecheScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name="flaeche", **kw)
        self.rand = InstructionGroup()
        self.canvas.add(self.rand)
        box = BoxLayout(orientation="vertical", size_hint=(0.8, 0.5),
                        pos_hint={"center_x": 0.5, "center_y": 0.5}, spacing=dp(12))
        self.info = Label(font_size=sp(22), halign="center", markup=True)
        self.info.bind(size=lambda l, s: setattr(l, "text_size", (s[0], None)))
        box.add_widget(self.info)
        knoepfe = BoxLayout(size_hint_y=0.35, spacing=dp(12))
        for text, aktion in (("Übernehmen", self.uebernehmen), ("Abbrechen", self.abbrechen)):
            b = Button(text=text, **LEISTE)
            b.bind(on_release=lambda _b, a=aktion: a())
            knoepfe.add_widget(b)
        box.add_widget(knoepfe)
        self.add_widget(box)
        self.bind(size=lambda *_: self.zeichne())
        self.kante = 0
        self.start = self.struts = None
        self.fehler = ""

    def on_pre_enter(self, *_):
        self.kante = 0
        self.fehler = ""
        try:
            self.start = niriconfig.struts_lesen()
            if not niriconfig.config_pfad().exists():
                raise FileNotFoundError(niriconfig.config_pfad())
            niriconfig.sichern()
        except OSError as e:
            self.start = None
            self.fehler = f"Keine niri-Konfiguration ({e}) – zuerst setup.sh ausführen."
        self.struts = dict(self.start or {})
        Window.bind(on_key_down=self.taste)
        self.zeichne()

    def on_leave(self, *_):
        Window.unbind(on_key_down=self.taste)

    def zeichne(self):
        self.rand.clear()
        w, h = self.size
        b = dp(3)
        linien = {"left": [b, 0, b, h], "right": [w - b, 0, w - b, h],
                  "top": [0, h - b, w, h - b], "bottom": [0, b, w, b]}
        aktiv = niriconfig.KANTEN[self.kante]
        for k, pts in linien.items():
            self.rand.add(Color(1, 0.85, 0) if k == aktiv else Color(1, 1, 1))
            self.rand.add(Line(points=pts, width=dp(3) if k == aktiv else dp(1.5)))
        if self.fehler:
            self.info.text = self.fehler + "\n\nEsc: zurück"
            return
        if self.struts is None:
            return
        werte = "   ".join(f"{KANTEN_DE[k]} {v}" for k, v in self.struts.items())
        self.info.text = (f"Kante: [b]{KANTEN_DE[aktiv]}[/b]\n{werte}\n\n"
                          "Tab: Kante wählen · Pfeile: ±1 px (Umschalt ±10 px)\n"
                          "Enter: übernehmen · Esc: abbrechen")

    def taste(self, _win, key, _scancode, _text, modifiers):
        if key == 27:
            self.abbrechen()
        elif key in (13, 271):
            self.uebernehmen()
        elif self.fehler:
            return False
        elif key == 9:
            self.kante = (self.kante + (-1 if "shift" in modifiers else 1)) % 4
            self.zeichne()
        else:
            kante = niriconfig.KANTEN[self.kante]
            schritt = TASTEN[kante].get(key)
            if schritt is None:
                return False
            if "shift" in modifiers:
                schritt *= 10
            self.struts[kante] = max(0, self.struts[kante] + schritt)
            niriconfig.struts_setzen(self.struts)
            self.zeichne()
        return True

    def abbrechen(self):
        if self.start is not None and self.struts != self.start:
            niriconfig.struts_setzen(self.start)
        App.get_running_app().zeige("menue")

    def uebernehmen(self):
        app = App.get_running_app()
        if self.start is not None and self.struts != self.start:
            app.flaeche_geaendert = True
        app.zeige("menue")


# --- Kalibrieren (D5, D6) -------------------------------------------------

KREUZE = [(0.1, 0.9), (0.9, 0.9), (0.9, 0.1), (0.1, 0.1)]   # normiert, y unten = 0
KONTROLLE = (0.5, 0.5)


class KalibrierScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name="kalibrieren", **kw)
        self.ziel = InstructionGroup()
        self.canvas.add(self.ziel)
        self.leiste = Leiste()
        self.leiste.knopf("Zurück", lambda: neustart())
        self.b_wiederholen = self.leiste.knopf("Wiederholen", self.zuruecksetzen)
        self.b_speichern = self.leiste.knopf("Speichern", self.speichern)
        self.add_widget(self.leiste)
        self.info = Label(font_size=sp(24), halign="center",
                          pos_hint={"center_x": 0.5, "center_y": 0.32}, size_hint=(0.7, 0.2))
        self.info.bind(size=lambda l, s: setattr(l, "text_size", (s[0], None)))
        self.add_widget(self.info)
        self.bind(size=lambda *_: self.zeichne())
        self.zuruecksetzen()

    def zuruecksetzen(self, meldung=""):
        self.roh, self.kal, self.ergebnis = [], None, None
        self.aktiv, self.verworfen = set(), False
        self.meldung = meldung
        self.zeichne()

    @property
    def schritt(self):
        return len(self.roh)

    def zeichne(self):
        self.ziel.clear()
        w, h = self.size
        fertig = self.ergebnis is not None
        for b in (self.b_speichern, self.b_wiederholen):
            b.disabled = not fertig
            b.opacity = 1 if fertig else 0.3
        if self.schritt < 4:
            x, y = KREUZE[self.schritt]
            kreuz(self.ziel, x * w, y * h)
            text = f"Kreuz {self.schritt + 1}/4 genau in der Mitte antippen"
        else:
            kreuz(self.ziel, KONTROLLE[0] * w, KONTROLLE[1] * h, (0.3, 0.9, 0.4))
            text = "Kontrollkreuz antippen"
        if fertig:
            px, schwelle, ist = self.ergebnis
            self.ziel.add(Color(1, 0.3, 0.3))
            self.ziel.add(Ellipse(pos=(ist[0] * w - dp(6), ist[1] * h - dp(6)),
                                  size=(dp(12), dp(12))))
            text = f"Abweichung {px:.1f} px (Schwelle {schwelle:.0f} px)\n"
            text += ("Wahrscheinlich Fehlberührung – bitte Wiederholen." if px > schwelle
                     else "Speichern oder Wiederholen.")
        self.info.text = "\n".join(t for t in (self.meldung, text) if t)

    def on_touch_down(self, touch):
        if self.leiste.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        self.aktiv.add(touch.uid)
        if len(self.aktiv) > 1:
            self.verworfen = True
        return True

    def on_touch_up(self, touch):
        if touch.uid not in self.aktiv:
            return super().on_touch_up(touch)
        self.aktiv.discard(touch.uid)
        if self.verworfen:
            if not self.aktiv:
                self.verworfen = False
                self.meldung = "Mehrere Finger erkannt – bitte dasselbe Kreuz mit einem Finger."
                self.zeichne()
            return True
        if self.ergebnis is not None:
            return True
        self.meldung = ""
        roh = (touch.sx, touch.sy)       # Rohmodus: sx/sy ohne Ausrichtung und postproc
        if self.schritt < 4:
            self.roh.append(roh)
            if self.schritt == 4:
                try:
                    self.kal = bestimme(KREUZE, self.roh)
                except ValueError as e:
                    self.zuruecksetzen(f"Keine Zuordnung möglich ({e}) – bitte neu.")
                    return True
        else:
            w, h = self.size
            ist = self.kal.anwenden(*roh)
            self.ergebnis = (abweichung_px(KONTROLLE, ist, w, h), schwelle_px(w, h), ist)
        self.zeichne()
        return True

    def speichern(self):
        try:
            cfg = kivyconfig.lesen()
            kivyconfig.setze_kalibrierung(cfg, **self.kal.werte())
            kivyconfig.schreiben(cfg)
        except (OSError, ValueError) as e:
            self.meldung = f"Speichern fehlgeschlagen: {e}"
            self.zeichne()
            return
        neustart("touchtest")


# --- Touchtest (D7) -------------------------------------------------------

ZIELE = [(x, y) for y in ("oben", 0.5, 0.05) for x in (0.05, 0.5, 0.95)]   # oben: unter der Leiste
DUPLIKAT_S = 0.1


class TouchtestScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name="touchtest", **kw)
        self.g_heatmap, self.g_spuren, self.g_marken = (InstructionGroup() for _ in range(3))
        self.g_ziele, self.g_finger = InstructionGroup(), InstructionGroup()
        for g in (self.g_heatmap, self.g_spuren, self.g_marken, self.g_ziele, self.g_finger):
            self.canvas.add(g)
        self.leiste = Leiste()
        self.leiste.knopf("Zurück", self.verlassen)
        self.leiste.knopf("Zurücksetzen", self.zuruecksetzen)
        for d in (10, 30, 60):
            self.leiste.knopf(f"Ruhe {d} s", lambda d=d: self.ruhe_start(d))
        self.b_ziele = self.leiste.knopf("Ziele", self.ziele_umschalten)
        self.add_widget(self.leiste)
        self.status = Label(font_size=sp(20), size_hint=(1, None), height=dp(36),
                            halign="center", markup=True)
        self.status.bind(size=lambda l, s: setattr(l, "text_size", s))
        self.add_widget(self.status)
        self.bind(size=lambda *_: self.alles_zeichnen())
        self.ruhe_ev = None
        self.zuruecksetzen()

    # Zustand

    def zuruecksetzen(self):
        for w in getattr(self, "id_labels", {}).values():
            self.remove_widget(w)
        self.finger = {}            # uid → (farbe, Ellipse, Line)
        self.id_labels = {}
        self.farbe_nr = 0
        self.maximum = 0
        self.heatmap = [[0] * RASTER[0] for _ in range(RASTER[1])]
        self.geister, self.ruhe_ende, self.ruhe_dauer, self.ruhe_pos = [], 0, 0, []
        self.ziele_an, self.abweichungen, self.getroffen = False, [], {}
        self.duplikate, self.letzte = 0, {"touch": -1.0, "mouse": -1.0}
        self.g_spuren.clear()
        self.g_marken.clear()
        self.g_finger.clear()
        self.alles_zeichnen()

    def on_pre_enter(self, *_):
        self.alles_zeichnen()

    def bericht(self):
        geraet = Config.get("input", kivyconfig.GERAET, fallback="")
        return Bericht(geraet=geraet, fenster=tuple(int(v) for v in self.size),
                       maximum=self.maximum, heatmap=[z[:] for z in self.heatmap],
                       geistertouches=list(self.geister), abweichungen=list(self.abweichungen),
                       doppelte_ereignisse=self.duplikate)

    def verlassen(self):
        app = App.get_running_app()
        try:
            pfad = self.bericht().speichern()
            app.meldungen = [f"Touchtest-Bericht: {pfad}"]
        except OSError as e:
            app.meldungen = [f"Bericht nicht gespeichert: {e}"]
        self.zuruecksetzen()
        app.zeige("menue")

    # Zeichnen

    def alles_zeichnen(self):
        if not hasattr(self, "heatmap"):
            return
        self.status.pos = (0, self.height - self.leiste.height - self.status.height)
        self.heatmap_zeichnen()
        self.ziele_zeichnen()
        self.status_zeigen()

    def heatmap_zeichnen(self):
        g = self.g_heatmap
        g.clear()
        w, h = self.size
        sp_, ze = RASTER
        zw, zh = w / sp_, h / ze
        for r in range(ze):
            for c in range(sp_):
                n = self.heatmap[r][c]
                g.add(Color(0.10, 0.35 + min(n, 50) / 100, 0.15) if n else Color(0.10, 0.10, 0.12))
                g.add(Rectangle(pos=(c * zw + 1, h - (r + 1) * zh + 1), size=(zw - 2, zh - 2)))

    def ziele_zeichnen(self):
        g = self.g_ziele
        g.clear()
        if not self.ziele_an:
            return
        for i, (x, y) in enumerate(self.ziele_px()):
            kreuz(g, x, y, (0.3, 0.9, 0.4) if i in self.getroffen else (1, 1, 1),
                  groesse=dp(22))

    def ziele_px(self):
        w, h = self.size
        oben = h - self.leiste.height - self.status.height - dp(30)
        return [(x * w, oben if y == "oben" else y * h) for x, y in ZIELE]

    def status_zeigen(self):
        teile = [f"Aktiv: {len(self.finger)}", f"Maximum: {self.maximum}",
                 f"Abdeckung: {sum(1 for z in self.heatmap for n in z if n) / (RASTER[0] * RASTER[1]):.0%}"]
        if self.ruhe_ende:
            rest = max(0, self.ruhe_ende - time.monotonic())
            teile.append(f"RUHE – nicht berühren! {rest:.0f} s, Geister: {len(self.ruhe_pos)}")
        elif self.geister:
            g = self.geister[-1]
            teile.append(f"Ruhe {g['dauer_s']} s: {g['anzahl']} Geistertouches")
        if self.abweichungen:
            teile.append(f"Ziele: {len(self.getroffen)}/9, max {max(a['px'] for a in self.abweichungen):.1f} px")
        if self.duplikate:
            teile.append(f"[color=ff5555]Doppelte Ereignisse (Maus+Touch): {self.duplikate}[/color]")
        self.status.text = "   ·   ".join(teile)

    # Ruhephase

    def ruhe_start(self, dauer):
        if self.ruhe_ev:
            self.ruhe_ev.cancel()
        self.ruhe_dauer, self.ruhe_pos = dauer, []
        self.ruhe_ende = time.monotonic() + dauer
        self.ruhe_ev = Clock.schedule_interval(self.ruhe_tick, 0.25)

    def ruhe_tick(self, _dt):
        if time.monotonic() >= self.ruhe_ende:
            self.ruhe_ev.cancel()
            self.ruhe_ev, self.ruhe_ende = None, 0
            self.geister.append({"dauer_s": self.ruhe_dauer, "anzahl": len(self.ruhe_pos),
                                 "positionen": self.ruhe_pos})
        self.status_zeigen()

    def ziele_umschalten(self):
        self.ziele_an = not self.ziele_an
        self.b_ziele.background_color = (0.2, 0.5, 0.25, 1) if self.ziele_an else LEISTE["background_color"]
        self.ziele_zeichnen()

    # Touches

    def _duplikat(self, touch):
        """Maus-Ereignis kurz nach einem echten Touch (oder umgekehrt) → Duplikat."""
        jetzt = time.monotonic()
        art = "mouse" if touch.device == "mouse" else "touch"
        andere = self.letzte["touch" if art == "mouse" else "mouse"]
        self.letzte[art] = jetzt
        return andere >= 0 and jetzt - andere < DUPLIKAT_S

    def _zelle(self, x, y):
        w, h = self.size
        c = min(RASTER[0] - 1, max(0, int(x / w * RASTER[0])))
        r = min(RASTER[1] - 1, max(0, int((1 - y / h) * RASTER[1])))
        self.heatmap[r][c] += 1
        return r, c

    def on_touch_down(self, touch):
        if self.leiste.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if self._duplikat(touch):
            self.duplikate += 1
            self.status_zeigen()
            if touch.device == "mouse":
                return True
        x, y = touch.pos
        if self.ruhe_ende:
            self.ruhe_pos.append([round(x), round(y)])
            self.g_marken.add(Color(1, 0.2, 0.2))
            self.g_marken.add(Line(points=[x - dp(12), y - dp(12), x + dp(12), y + dp(12)], width=dp(2)))
            self.g_marken.add(Line(points=[x - dp(12), y + dp(12), x + dp(12), y - dp(12)], width=dp(2)))
            self.status_zeigen()
            return True
        if self.ziele_an:
            w, h = self.size
            ziele = self.ziele_px()
            i = min(range(len(ziele)), key=lambda k: (ziele[k][0] - x) ** 2 + (ziele[k][1] - y) ** 2)
            ziel = ziele[i]
            px = abweichung_px((ziel[0] / w, ziel[1] / h), (x / w, y / h), w, h)
            self.abweichungen.append({"ziel": [round(ziel[0]), round(ziel[1])],
                                      "ist": [round(x), round(y)], "px": round(px, 1)})
            self.getroffen[i] = px
            self.ziele_zeichnen()
        farbe = PALETTE[self.farbe_nr % len(PALETTE)]
        self.farbe_nr += 1
        self.g_spuren.add(Color(*farbe))
        spur = Line(points=[x, y], width=dp(2))
        self.g_spuren.add(spur)
        self.g_finger.add(Color(*farbe))
        r = dp(28)
        punkt = Ellipse(pos=(x - r, y - r), size=(2 * r, 2 * r))
        self.g_finger.add(punkt)
        lbl = Label(text=str(touch.id), font_size=sp(18), size_hint=(None, None),
                    size=(dp(80), dp(24)), center=(x, y + r + dp(14)))
        self.add_widget(lbl)
        self.finger[touch.uid] = (punkt, spur)
        self.id_labels[touch.uid] = lbl
        self.maximum = max(self.maximum, len(self.finger))
        self._zelle(x, y)
        self.heatmap_zeichnen()
        self.status_zeigen()
        return True

    def on_touch_move(self, touch):
        if touch.uid not in self.finger:
            return super().on_touch_move(touch)
        punkt, spur = self.finger[touch.uid]
        x, y = touch.pos
        r = punkt.size[0] / 2
        punkt.pos = (x - r, y - r)
        spur.points += [x, y]
        self.id_labels[touch.uid].center = (x, y + r + dp(14))
        self._zelle(x, y)
        self.heatmap_zeichnen()
        return True

    def on_touch_up(self, touch):
        if touch.uid not in self.finger:
            return super().on_touch_up(touch)
        punkt, _spur = self.finger.pop(touch.uid)
        self.g_finger.remove(punkt)
        self.remove_widget(self.id_labels.pop(touch.uid))
        self.status_zeigen()
        return True


# --- App ------------------------------------------------------------------

class InbetriebApp(App):
    title = "Inbetriebnahme"

    def __init__(self, modus=None, **kw):
        super().__init__(**kw)
        self.modus = modus
        self.flaeche_geaendert = False
        self.meldungen = []
        self.niri_beenden = False

    def build(self):
        Window.clearcolor = (0, 0, 0, 1)
        self.sm = ScreenManager(transition=NoTransition())
        for s in (MenueScreen(), FlaecheScreen(), TouchtestScreen()):
            self.sm.add_widget(s)
        if self.modus == "kalibrieren":
            self.sm.add_widget(KalibrierScreen())
        self.sm.current = self.modus or "menue"
        return self.sm

    def zeige(self, name):
        self.sm.current = name

    def beenden(self):
        self.niri_beenden = bool(os.environ.get("NIRI_SOCKET"))
        self.stop()

    def on_stop(self):
        if self.sm.current == "touchtest":
            try:
                print("Touchtest-Bericht:", self.sm.current_screen.bericht().speichern())
            except OSError:
                pass
        if self.niri_beenden:
            subprocess.run(["niri", "msg", "action", "quit", "--skip-confirmation"],
                           timeout=5, check=False)

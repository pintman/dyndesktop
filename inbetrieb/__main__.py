"""Start: python -m inbetrieb [--flaeche | --kalibrieren | --touchtest] [-- <Kivy-Optionen>]

Kein Vollbild: unter niri läuft das Fenster maximiert in der Rahmenfläche (D12).
--kalibrieren startet im Rohmodus: Kalibrierung nur im Speicher entfernt (D5).
"""
import argparse
import sys


def main():
    p = argparse.ArgumentParser(prog="python -m inbetrieb")
    modus = p.add_mutually_exclusive_group()
    for m in ("flaeche", "kalibrieren", "touchtest"):
        modus.add_argument(f"--{m}", dest="modus", action="store_const", const=m)
    args, rest = p.parse_known_args()
    sys.argv = [sys.argv[0], *rest]          # Rest geht an Kivy

    # Nur im Speicher; muss vor dem Import von kivy.core.window passieren.
    from kivy.config import Config
    Config.set("graphics", "fullscreen", "0")
    Config.set("kivy", "exit_on_escape", "0")      # Esc gehört dem Flächen-Screen
    if args.modus == "kalibrieren":
        from .kivyconfig import rohmodus
        rohmodus(Config)
        Config.filename = None                      # Rohwerte nie zurückschreiben

    from .app import InbetriebApp
    InbetriebApp(args.modus).run()


if __name__ == "__main__":
    main()

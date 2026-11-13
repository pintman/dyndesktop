"""Start: python -m tisch [--inhalte <ordner>] [-- <Kivy-Optionen>]

Vollbild nur von außen, z. B. KCFG_GRAPHICS_FULLSCREEN=auto.
"""
import argparse
import sys
from pathlib import Path

PROJEKT = Path(__file__).resolve().parent.parent


def main():
    p = argparse.ArgumentParser(prog="python -m tisch")
    p.add_argument("--inhalte", type=Path, default=PROJEKT / "inhalte",
                   help="Inhaltsordner (Standard: %(default)s)")
    args, rest = p.parse_known_args()
    sys.argv = [sys.argv[0], *rest]          # Rest geht an Kivy

    # Tastaturmodus nur im Speicher, config.ini bleibt unberührt (D6).
    # Muss vor dem Import von Window und TextInput passieren.
    from kivy.config import Config
    Config.set("kivy", "keyboard_mode", "systemandmulti")
    Config.set("kivy", "keyboard_layout", "qwertz")

    from kivy.core.window import Window

    from .tastatur import TischTastatur
    Window.set_vkeyboard_class(TischTastatur)

    from .app import TischApp
    TischApp(args.inhalte.expanduser().resolve()).run()


if __name__ == "__main__":
    main()

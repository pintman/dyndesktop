"""Kivy headless: keine Argumente parsen, eigenes KIVY_HOME, feste Dichte."""
import os
import tempfile

os.environ.setdefault("KIVY_NO_ARGS", "1")
os.environ.setdefault("KIVY_NO_CONSOLELOG", "1")
os.environ.setdefault("KIVY_NO_FILELOG", "1")
os.environ.setdefault("KIVY_METRICS_DENSITY", "1")
os.environ["KIVY_HOME"] = tempfile.mkdtemp(prefix="kivy-test-")
# Kivy-Widgets brauchen einen GL-Kontext (Widget.__init__ → ensure_window).
# Das Fenster bleibt unsichtbar.
os.environ.setdefault("KCFG_GRAPHICS_WINDOW_STATE", "hidden")

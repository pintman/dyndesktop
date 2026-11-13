"""Inhaltsordner: scannen, Dateinamen prüfen, Text speichern. Nur Standardbibliothek."""
import os
import tempfile
from pathlib import Path


class DateinameFehler(ValueError):
    """Dateiname abgelehnt. Die Meldung ist der Hinweistext."""


def scanne(ordner, endungen) -> list[Path]:
    """Unterstützte Dateien direkt im Ordner, sortiert nach Name."""
    ordner = Path(ordner)
    if not ordner.is_dir():
        return []
    erlaubt = {e.lower() for e in endungen}
    return sorted((p for p in ordner.iterdir()
                   if p.is_file() and p.suffix.lower() in erlaubt),
                  key=lambda p: p.name)


def pruefe_dateiname(ordner, name: str, typ) -> Path:
    """Liefert den Pfad zu `name` im Ordner oder wirft DateinameFehler (D3)."""
    ordner = Path(ordner)
    name = name.strip()
    if not name:
        raise DateinameFehler("Bitte einen Dateinamen eingeben.")
    if "/" in name or "\\" in name or ".." in name or Path(name).is_absolute():
        raise DateinameFehler("Nur ein Dateiname ohne Pfad ist erlaubt.")
    pfad = ordner / name
    if not pfad.exists():
        raise DateinameFehler(f"Datei {name} fehlt im Inhaltsordner.")
    if pfad.resolve().parent != ordner.resolve():
        raise DateinameFehler(f"{name} verweist aus dem Inhaltsordner heraus.")
    if not pfad.is_file():
        raise DateinameFehler(f"{name} ist keine Datei.")
    if pfad.suffix.lower() not in {e.lower() for e in typ.endungen}:
        erlaubt = ", ".join(typ.endungen)
        raise DateinameFehler(
            f"{name} passt nicht zum Kartentyp '{typ.name}' (erlaubt: {erlaubt}).")
    return pfad


def schreibe_text(pfad, text: str) -> None:
    """Schreibt UTF-8 atomar (D4). Wirft PermissionError bei schreibgeschützter Datei."""
    pfad = Path(pfad)
    if pfad.exists() and not os.access(pfad, os.W_OK):
        raise PermissionError(f"{pfad.name} ist schreibgeschützt.")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    fd, tmp = tempfile.mkstemp(dir=pfad.parent, prefix=f".{pfad.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        if pfad.exists():
            os.chmod(tmp, pfad.stat().st_mode & 0o777)
        os.replace(tmp, pfad)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise

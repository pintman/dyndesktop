"""Ein neuer Kartentyp braucht nur Klasse + registriere (Spec kartentypen)."""
import pytest
from kivy.uix.label import Label

from tisch import typen
from tisch.app import lade_karten
from tisch.karte import SchwungKarte


class MarkdownTyp(typen.Kartentyp):
    name = "markdown"
    endungen = (".md",)

    def erzeuge_inhalt(self, pfad):
        return Label(text=pfad.read_text(encoding="utf-8"))


@pytest.fixture
def registry(monkeypatch):
    monkeypatch.setattr(typen._standard, "_typen", dict(typen._standard._typen))
    return typen._standard


def test_neuer_typ_wird_karte(registry, tmp_path):
    typen.registriere(MarkdownTyp())
    (tmp_path / "notiz.md").write_text("# Hallo", encoding="utf-8")
    (tmp_path / "x.unbekannt").write_text("?")

    karten = lade_karten(tmp_path)

    assert len(karten) == 1
    k = karten[0]
    assert isinstance(k, SchwungKarte)
    assert isinstance(k.typ, MarkdownTyp)
    assert k.inhalt.text == "# Hallo"
    assert k.do_rotation and k.do_scale and k.do_translation_x
    assert (k.scale_min, k.scale_max) == (0.3, 4)


def test_doppelte_endung_global(registry):
    with pytest.raises(ValueError):
        typen.registriere(MarkdownTyp.__new__(type("T", (MarkdownTyp,), {"endungen": (".TXT",)})))


def test_eingebaute_typen():
    assert typen.typ_fuer("a.TXT").name == "text"
    assert typen.typ_fuer("a.jpeg").name == "bild"
    assert typen.typ_fuer("a.webm").name == "video"

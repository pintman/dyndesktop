import pytest

from tisch.typen import Kartentyp, Registry


class Dummy(Kartentyp):
    def __init__(self, name, endungen):
        self.name, self.endungen = name, endungen


def test_zuordnung():
    r = Registry()
    bild = r.registriere(Dummy("bild", (".png", ".jpg")))
    assert r.typ_fuer("a/b.png") is bild
    assert r.typ_fuer("x.jpg") is bild
    assert r.typ_fuer("x.txt") is None


def test_gross_kleinschreibung():
    r = Registry()
    t = r.registriere(Dummy("bild", (".JPG",)))
    assert r.typ_fuer("FOTO.jpg") is t
    assert r.typ_fuer("foto.Jpg") is t
    assert r.endungen() == {".jpg"}


def test_doppelte_endung():
    r = Registry()
    r.registriere(Dummy("bild", (".png",)))
    with pytest.raises(ValueError, match="bild"):
        r.registriere(Dummy("anders", (".gif", ".PNG")))
    assert r.typ_fuer("x.gif") is None      # nichts halb angemeldet


def test_neuer_typ_neue_endung():
    r = Registry()
    r.registriere(Dummy("bild", (".png",)))
    md = r.registriere(Dummy("markdown", (".md",)))
    assert r.typ_fuer("notiz.md") is md

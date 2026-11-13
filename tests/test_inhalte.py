import os

import pytest

from tisch.inhalte import DateinameFehler, pruefe_dateiname, scanne, schreibe_text


class Typ:
    def __init__(self, name, endungen):
        self.name, self.endungen = name, endungen


BILD = Typ("bild", (".jpg", ".jpeg", ".png"))
ENDUNGEN = {".txt", ".png", ".mp4"}


# --- scanne ---------------------------------------------------------------

def test_scanne_gemischt(tmp_path):
    for n in ["b.png", "a.txt", "c.MP4", "d.doc", "e"]:
        (tmp_path / n).write_text("x")
    (tmp_path / "unter").mkdir()
    (tmp_path / "unter" / "f.png").write_text("x")
    assert [p.name for p in scanne(tmp_path, ENDUNGEN)] == ["a.txt", "b.png", "c.MP4"]


def test_scanne_leer(tmp_path):
    assert scanne(tmp_path, ENDUNGEN) == []


def test_scanne_fehlt(tmp_path):
    assert scanne(tmp_path / "gibtsnicht", ENDUNGEN) == []


# --- pruefe_dateiname -------------------------------------------------------

@pytest.fixture
def ordner(tmp_path):
    o = tmp_path / "inhalte"
    o.mkdir()
    (o / "foto.png").write_bytes(b"x")
    (o / "film.mp4").write_bytes(b"x")
    (tmp_path / "x.png").write_bytes(b"x")
    return o


def test_gueltig(ordner):
    assert pruefe_dateiname(ordner, "foto.png", BILD) == ordner / "foto.png"


def test_fehlt(ordner):
    with pytest.raises(DateinameFehler, match="fehlt"):
        pruefe_dateiname(ordner, "nix.png", BILD)


def test_pfad_relativ(ordner):
    with pytest.raises(DateinameFehler, match="ohne Pfad"):
        pruefe_dateiname(ordner, "../x.png", BILD)


def test_pfad_absolut(ordner):
    with pytest.raises(DateinameFehler, match="ohne Pfad"):
        pruefe_dateiname(ordner, str(ordner.parent / "x.png"), BILD)


def test_symlink_nach_aussen(ordner):
    (ordner / "link.png").symlink_to(ordner.parent / "x.png")
    with pytest.raises(DateinameFehler, match="heraus"):
        pruefe_dateiname(ordner, "link.png", BILD)


def test_falscher_typ(ordner):
    with pytest.raises(DateinameFehler, match="Kartentyp 'bild'"):
        pruefe_dateiname(ordner, "film.mp4", BILD)


# --- schreibe_text ----------------------------------------------------------

def test_umlaute(tmp_path):
    p = tmp_path / "t.txt"
    p.write_text("alt", encoding="utf-8")
    schreibe_text(p, "Größe\r\nÄrger ß")
    assert p.read_bytes() == "Größe\nÄrger ß".encode("utf-8")
    assert [q.name for q in tmp_path.iterdir()] == ["t.txt"]


@pytest.mark.skipif(os.geteuid() == 0, reason="root darf alles schreiben")
def test_schreibgeschuetzt(tmp_path):
    p = tmp_path / "t.txt"
    p.write_text("alt", encoding="utf-8")
    p.chmod(0o444)
    try:
        with pytest.raises(PermissionError):
            schreibe_text(p, "neu")
        assert p.read_text(encoding="utf-8") == "alt"
        assert [q.name for q in tmp_path.iterdir()] == ["t.txt"]
    finally:
        p.chmod(0o644)

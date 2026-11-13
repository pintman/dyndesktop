from tisch.langdruck import Erkenner


def e():
    return Erkenner(dauer=0.8, schwelle=10)


def test_ausloesen():
    k = e()
    k.down(1, (100, 100), t=0.0)
    assert not k.faellig(0.79)
    k.move(1, (106, 107))                 # 9,2 px < 10
    assert k.faellig(0.8)
    assert not k.faellig(2.0)             # nur einmal


def test_bewegung_ueber_schwelle():
    k = e()
    k.down(1, (100, 100), t=0.0)
    k.move(1, (111, 100))
    assert not k.faellig(1.0)


def test_zweiter_finger():
    k = e()
    k.down(1, (100, 100), t=0.0)
    k.down(2, (150, 100), t=0.1)
    assert not k.faellig(1.0)
    k.up(2)                                # erster Finger allein reicht nicht erneut
    assert not k.faellig(2.0)


def test_loslassen_vor_ablauf():
    k = e()
    k.down(1, (100, 100), t=0.0)
    k.up(1)
    assert not k.faellig(1.0)


def test_nach_ausloesen_neuer_druck():
    k = e()
    k.down(1, (0, 0), t=0.0)
    assert k.faellig(1.0)                  # Finger 1 gilt als verbraucht (kein up mehr)
    k.down(2, (0, 0), t=5.0)
    assert k.faellig(5.81)

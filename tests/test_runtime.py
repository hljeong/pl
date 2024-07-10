from pytest import raises

from runtime import Ins


def test_fragment_validation():
    with raises(ValueError):
        Ins.Frag(0b1101, 3)

    with raises(ValueError):
        Ins.Frag(-1, 7)

    with raises(ValueError):
        (Ins.Frag(0b10101, 5) + Ins.Frag(0b011, 3) + Ins.Frag(0b1100101, 7))(n_bytes=2)

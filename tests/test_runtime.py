from pytest import raises, fixture

from common import Log
from runtime import Ins


@fixture
def log_w():
    Log.level = Log.Level.WARN
    yield
    Log.level = Log.Level.ERROR


def test_fragment_validation():
    with raises(ValueError):
        Ins.Frag(0b1101, 3)

    with raises(ValueError):
        Ins.Frag(-1, 7)

    with raises(ValueError):
        (Ins.Frag(0b10101, 5) + Ins.Frag(0b011, 3) + Ins.Frag(0b1100101, 7))(n_bytes=2)

    assert Log.level == Log.Level.ERROR


def test_fragment_byte_boundary(log_w, capsys):
    # make diagnostics happy
    _ = log_w
    _ = Ins.Frag(0b101, 3) + Ins.Frag(0b110111, 6)
    out, _ = capsys.readouterr()
    assert out.startswith("[WARN]")

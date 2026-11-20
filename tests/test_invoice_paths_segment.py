import pytest

from stackin.core.client import _invoice_segment


def test_an_invoice_id_stays_one_segment():
    assert _invoice_segment("a/b") == "a%2Fb"


@pytest.mark.parametrize("value", ["..", "."])
def test_dot_segments_are_refused(value):
    with pytest.raises(ValueError):
        _invoice_segment(value)

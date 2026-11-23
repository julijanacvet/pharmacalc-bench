"""Smoke test for the PharmaCalc-Bench package skeleton."""

import pharmacalc


def test_package_version() -> None:
    """The package imports and reports the expected development version."""
    assert pharmacalc.__version__ == "0.1.0"

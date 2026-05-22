"""Smoke test: the package imports and exposes a version string.

This test exists to verify the test harness end-to-end (pytest discovery,
src/ layout, package install). Real model tests start in milestone 2.
"""

import ord


def test_package_has_version():
    assert isinstance(ord.__version__, str)
    assert ord.__version__

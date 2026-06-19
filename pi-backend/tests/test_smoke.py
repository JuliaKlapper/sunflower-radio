"""Smoke test — proves the package imports and the gate runs real test code.

Replaced/expanded by the real unit suites in Phases 4-6 (test_state.py,
test_dispatch.py, test_broadcaster.py, test_events.py, test_api.py, ...).
"""

import sunflower_radio


def test_package_imports() -> None:
    assert sunflower_radio.__version__ == "0.1.0"

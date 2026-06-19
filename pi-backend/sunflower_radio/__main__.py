"""Composition root for the sunflower-radio service.

Phase 4 establishes only the radio_cli path-resolution policy (Q13.3d). The full
wiring — RadioState, EvdevEventSource, Broadcaster, FastAPI, the asyncio run loop
— lands in Phases 5-6.
"""

import os

# The stable symlink confirmed in Phase 1 (→ radio_cli_v3.2.1); a single
# hardcoded default, overridable for dev/test via RADIO_CLI_PATH.
DEFAULT_RADIO_CLI_PATH = "/usr/local/sbin/radio_cli"


def resolve_radio_cli_path() -> str:
    """RADIO_CLI_PATH env override → the stable default constant."""
    return os.environ.get("RADIO_CLI_PATH", DEFAULT_RADIO_CLI_PATH)

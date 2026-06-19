"""The input seam: normalized rotary/button events + the decode of raw evdev.

`decode()` is a pure function over the raw Linux input-event triple
`(type, code, value)` — deliberately free of any `evdev` import so the mapping is
unit-testable on a macOS dev machine (evdev is Linux-only; see `pyproject.toml`).
`EvdevEventSource` is the only thing that touches `evdev`, and it imports it
lazily inside its methods so this module stays importable everywhere.

The decode reuses the Phase-1-restored `process_events` logic from the good
`4ca7605` baseline (`legacy/simple-dab-radio.py:174-203`): a `REL_X` delta is a
rotation, `KEY_ENTER` is the push button. Rotations are normalized to a single
±1 detent (the hardware emits ±1 per click; see Phase-1 evdev probe).
"""

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Protocol

# Raw Linux input-event constants (stable kernel ABI; mirrored here so this
# module needs no evdev import). evdev.ecodes defines the same values.
EV_KEY = 0x01
EV_REL = 0x02
REL_X = 0x00
KEY_ENTER = 28
_KEY_UP = 0  # keystate value for a release


@dataclass(frozen=True)
class RotaryEvent:
    """One detent of the encoder. `direction` is +1 (cw) or -1 (ccw)."""

    direction: int


@dataclass(frozen=True)
class ButtonEvent:
    """A push-button state transition. `pressed` True = down, False = release."""

    pressed: bool


Event = RotaryEvent | ButtonEvent


def decode(ev_type: int, code: int, value: int) -> Event | None:
    """Map a raw `(type, code, value)` input event to a normalized event, or None.

    Returns None for anything we don't act on (other axes/keys, zero-delta turns).
    """
    if ev_type == EV_REL and code == REL_X:
        if value > 0:
            return RotaryEvent(direction=1)
        if value < 0:
            return RotaryEvent(direction=-1)
        return None
    if ev_type == EV_KEY and code == KEY_ENTER:
        return ButtonEvent(pressed=value != _KEY_UP)
    return None


class EventSource(Protocol):
    """Async source of normalized input events (the dispatch loop consumes this)."""

    def events(self) -> AsyncIterator[Event]: ...


class FakeEventSource:
    """Test double: replays a scripted, finite sequence of events then stops."""

    def __init__(self, scripted: Sequence[Event]) -> None:
        self._scripted = list(scripted)

    async def events(self) -> AsyncIterator[Event]:
        for event in self._scripted:
            yield event


class EvdevEventSource:
    """Linux-only: decode raw evdev events from all input devices into our events.

    On a Pi with a rotary encoder there are two input devices (rotation + push);
    we merge them. `evdev` is imported lazily so this class is the seam's only
    Linux dependency — the rest of the package imports `events` freely on macOS.
    """

    async def events(self) -> AsyncIterator[Event]:
        import asyncio

        import evdev

        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        if not devices:
            return

        queue: asyncio.Queue[Event] = asyncio.Queue()

        async def pump(device: "evdev.InputDevice") -> None:
            async for raw in device.async_read_loop():
                event = decode(raw.type, raw.code, raw.value)
                if event is not None:
                    await queue.put(event)

        tasks = [asyncio.create_task(pump(device)) for device in devices]
        try:
            while True:
                yield await queue.get()
        finally:
            for task in tasks:
                task.cancel()

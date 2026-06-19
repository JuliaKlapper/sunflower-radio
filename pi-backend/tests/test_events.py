"""Unit tests for the event-source seam decode logic (Q13.5).

`events.decode` is a pure function over raw Linux input codes (type/code/value),
deliberately free of any `evdev` import so it runs on a macOS dev machine where
`evdev` is not installed. The Linux-only `EvdevEventSource` feeds it
`(event.type, event.code, event.value)` triples; this test pins the mapping.
"""

import pytest

from sunflower_radio.events import (
    EV_KEY,
    EV_REL,
    KEY_ENTER,
    REL_X,
    ButtonEvent,
    Event,
    FakeEventSource,
    RotaryEvent,
    decode,
)


@pytest.mark.parametrize(
    ("ev_type", "code", "value", "expected"),
    [
        (EV_REL, REL_X, 1, RotaryEvent(direction=1)),
        (EV_REL, REL_X, -1, RotaryEvent(direction=-1)),
        (EV_REL, REL_X, 5, RotaryEvent(direction=1)),  # normalized to a single detent
        (EV_REL, REL_X, -3, RotaryEvent(direction=-1)),
        (EV_KEY, KEY_ENTER, 1, ButtonEvent(pressed=True)),  # press down
        (EV_KEY, KEY_ENTER, 0, ButtonEvent(pressed=False)),  # release
    ],
)
def test_decode_maps_raw_codes_to_normalized_events(
    ev_type: int, code: int, value: int, expected: object
) -> None:
    assert decode(ev_type, code, value) == expected


@pytest.mark.parametrize(
    ("ev_type", "code", "value"),
    [
        (EV_REL, REL_X, 0),  # a zero-delta rotation is not a detent
        (EV_KEY, 999, 1),  # some other key
        (EV_REL, 999, 1),  # some other relative axis
        (0x99, 0, 0),  # unknown event type
    ],
)
def test_decode_ignores_irrelevant_events(ev_type: int, code: int, value: int) -> None:
    assert decode(ev_type, code, value) is None


async def test_fake_event_source_yields_scripted_sequence() -> None:
    scripted: list[Event] = [
        RotaryEvent(direction=1),
        ButtonEvent(pressed=False),
        RotaryEvent(direction=-1),
    ]
    source = FakeEventSource(scripted)
    collected = [event async for event in source.events()]
    assert collected == scripted

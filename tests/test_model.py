"""Test Motion Dimmer models."""

import logging
from datetime import timedelta
from unittest.mock import PropertyMock, patch

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_COLOR_TEMP,
    ATTR_RGB_COLOR,
    ColorMode,
)
from homeassistant.util.dt import now

from custom_components.motion_dimmer.const import (
    DEFAULT_PREDICTION_BRIGHTNESS,
    DEFAULT_PREDICTION_SECS,
    DEFAULT_SEG_SECONDS,
    LONG_TIME_OFF,
    PUMP_TIME,
    SENSOR_ACTIVE,
    SMALL_TIME_OFF,
)
from custom_components.motion_dimmer.models import (
    DimmerStateChange,
    MotionDimmer,
    TimerState,
)
from tests import (
    MockAdapter,
    entry_keys,
    get_entry_value,
)

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR, force=True)

TRIGGER_EVENTS = [
    "turn_on_dimmer",
    "cancel_timer",
    "schedule_timer",
    "track_timer",
    "cancel_periodic_timer",
    "schedule_periodic_timer",
    "turn_on_script",
]

TURN_OFF_EVENTS = [
    "cancel_timer",
    "cancel_periodic_timer",
    "turn_off_dimmer",
    "track_timer",
]


async def test_color_modes():
    """Test default settings."""

    mock_adapter = MockAdapter()
    motion_dimmer = MotionDimmer(mock_adapter)

    # Test default white.
    motion_dimmer.triggered_callback()
    events = mock_adapter.flush_entries()

    assert entry_keys(events) == TRIGGER_EVENTS
    assert get_entry_value(events, "turn_on_dimmer", ATTR_BRIGHTNESS) == 255
    assert get_entry_value(events, "turn_on_dimmer", ATTR_COLOR_MODE) == ColorMode.WHITE
    assert get_entry_value(events, "schedule_timer", "secs") == DEFAULT_SEG_SECONDS
    assert get_entry_value(events, "track_timer", "secs") == DEFAULT_SEG_SECONDS
    assert get_entry_value(events, "schedule_periodic_timer", "secs") == 59

    # Test color temp.
    mock_adapter.color_mode = ColorMode.COLOR_TEMP
    mock_adapter.color_temp = 500
    mock_adapter.brightness = 33

    motion_dimmer.triggered_callback()
    events = mock_adapter.flush_entries()

    assert entry_keys(events) == TRIGGER_EVENTS
    assert get_entry_value(events, "turn_on_dimmer", ATTR_BRIGHTNESS) == 33
    assert (
        get_entry_value(events, "turn_on_dimmer", ATTR_COLOR_MODE)
        == ColorMode.COLOR_TEMP
    )
    assert get_entry_value(events, "turn_on_dimmer", ATTR_COLOR_TEMP) == 500

    # Test rgb color.
    mock_adapter.color_mode = ColorMode.RGB
    mock_adapter.color_temp = 500
    mock_adapter.rgb_color = (255, 0, 0)
    mock_adapter.brightness = 44

    motion_dimmer.triggered_callback()
    events = mock_adapter.flush_entries()

    assert entry_keys(events) == TRIGGER_EVENTS
    assert get_entry_value(events, "turn_on_dimmer", ATTR_BRIGHTNESS) == 44
    assert get_entry_value(events, "turn_on_dimmer", ATTR_COLOR_MODE) == ColorMode.RGB
    assert get_entry_value(events, "turn_on_dimmer", ATTR_RGB_COLOR) == (255, 0, 0)


async def test_trigger():
    """Test finishing while trigger is active."""

    mock_adapter = MockAdapter()
    motion_dimmer = MotionDimmer(mock_adapter)

    # Finish a timer with trigger still on.
    mock_adapter.are_triggers_on = True
    motion_dimmer.timer_callback()
    events = mock_adapter.flush_entries()

    # Dimmer is restarted instead of stopped.
    assert entry_keys(events) == TRIGGER_EVENTS

    # Finish a timer with trigger still on but Motion Dimmer disabled.
    mock_adapter.are_triggers_on = True
    mock_adapter.is_on = False
    motion_dimmer.timer_callback()
    events = mock_adapter.flush_entries()

    # Timer is updated to "idle".
    assert entry_keys(events) == ["track_timer"]

    # Finish a timer with trigger still on but segment disabled.
    mock_adapter.are_triggers_on = True
    mock_adapter.is_segment_enabled = False
    mock_adapter.is_on = True
    motion_dimmer.stop_dimmer()
    events = mock_adapter.flush_entries()

    # Dimmer is stopped.
    assert entry_keys(events) == TURN_OFF_EVENTS


async def test_predictor():
    """Test predictor settings."""

    # Test predictor when dimmer is off.
    mock_adapter = MockAdapter()
    motion_dimmer = MotionDimmer(mock_adapter)
    motion_dimmer.predictor_callback()
    events = mock_adapter.flush_entries()

    prediction_events = [
        "turn_on_dimmer",
        "cancel_timer",
        "schedule_timer",
        "track_timer",
    ]

    # Dimmer is turned on to prediction brightness for prediction seconds.
    assert entry_keys(events) == prediction_events
    assert (
        get_entry_value(events, "turn_on_dimmer", "brightness")
        == DEFAULT_PREDICTION_BRIGHTNESS
    )
    assert get_entry_value(events, "schedule_timer", "secs") == DEFAULT_PREDICTION_SECS
    assert get_entry_value(events, "track_timer", "secs") == DEFAULT_PREDICTION_SECS

    # Let prediction complete.
    motion_dimmer.timer_callback()
    events = mock_adapter.flush_entries()

    # Dimmer is turned off.
    assert entry_keys(events) == TURN_OFF_EVENTS

    # Test prediction brightness lower than minimum.
    mock_adapter = MockAdapter()
    motion_dimmer = MotionDimmer(mock_adapter)
    mock_adapter.brightness_min = 50
    mock_adapter.prediction_brightness = 10
    motion_dimmer.predictor_callback()
    events = mock_adapter.flush_entries()

    assert entry_keys(events) == prediction_events
    assert get_entry_value(events, "turn_on_dimmer", "brightness") == 50

    # Test prediction brightness higher than segment.
    mock_adapter = MockAdapter()
    motion_dimmer = MotionDimmer(mock_adapter)
    mock_adapter.brightness = 10
    mock_adapter.prediction_brightness = 50
    motion_dimmer.predictor_callback()
    events = mock_adapter.flush_entries()

    assert entry_keys(events) == prediction_events
    assert get_entry_value(events, "turn_on_dimmer", "brightness") == 10

    # Test predictor when dimmer is on.
    mock_adapter = MockAdapter()
    motion_dimmer = MotionDimmer(mock_adapter)
    mock_adapter.is_dimmer_on = True
    motion_dimmer.predictor_callback()
    events = mock_adapter.flush_entries()

    # Nothing is changed.
    assert entry_keys(events) == []

    # Test dimmer when predictor is on.
    mock_adapter = MockAdapter()
    motion_dimmer = MotionDimmer(mock_adapter)
    motion_dimmer.predictor_callback()
    events = mock_adapter.flush_entries()

    # Dimmer is turned on to prediction brightness for prediction seconds.
    assert entry_keys(events) == prediction_events
    assert (
        get_entry_value(events, "turn_on_dimmer", "brightness")
        == DEFAULT_PREDICTION_BRIGHTNESS
    )
    assert get_entry_value(events, "schedule_timer", "secs") == DEFAULT_PREDICTION_SECS
    assert get_entry_value(events, "track_timer", "secs") == DEFAULT_PREDICTION_SECS
    assert get_entry_value(events, "schedule_periodic_timer", "secs") is None

    # Dimmer is now on at prediction brightness.
    mock_adapter.is_dimmer_on = True

    # Trigger the dimmer.
    motion_dimmer.triggered_callback()
    events = mock_adapter.flush_entries()

    # Dimmer is turned on normally.
    assert entry_keys(events) == TRIGGER_EVENTS
    assert get_entry_value(events, "turn_on_dimmer", ATTR_BRIGHTNESS) == 255
    assert get_entry_value(events, "schedule_timer", "secs") == DEFAULT_SEG_SECONDS
    assert get_entry_value(events, "schedule_periodic_timer", "secs") == 59


async def test_pump():
    """Test predictor settings."""

    # Test pump when dimmer brightness is lower than minimum.
    mock_adapter = MockAdapter()
    motion_dimmer = MotionDimmer(mock_adapter)
    mock_adapter.brightness = 10
    mock_adapter.brightness_min = 20
    motion_dimmer.triggered_callback()
    events = mock_adapter.flush_entries()

    # Dimmer is turned on to prediction brightness for prediction seconds.
    assert entry_keys(events) == [
        "turn_on_dimmer",
        "schedule_pump_timer",
    ]
    assert get_entry_value(events, "turn_on_dimmer", "brightness") == 20
    assert get_entry_value(events, "schedule_pump_timer", "secs") == PUMP_TIME

    # Finish the pump.
    motion_dimmer.pump_callback()
    events = mock_adapter.flush_entries()

    # Dimmer is turned on to correct brightness for default seconds.
    assert entry_keys(events) == [
        "turn_on_dimmer",
        "cancel_timer",
        "schedule_timer",
        "track_timer",
        "cancel_periodic_timer",
        "schedule_periodic_timer",
        "turn_on_script",
    ]

    assert get_entry_value(events, "turn_on_dimmer", "brightness") == 10
    assert get_entry_value(events, "schedule_timer", "secs") == DEFAULT_SEG_SECONDS


async def test_disable():
    """Test disable settings."""

    mock_adapter = MockAdapter()
    motion_dimmer = MotionDimmer(mock_adapter)

    # Test disable motion dimmer.
    mock_adapter.is_on = False
    motion_dimmer.triggered_callback()
    motion_dimmer.predictor_callback()
    motion_dimmer.periodic_callback()
    events = mock_adapter.flush_entries()

    # Nothing happens.
    assert entry_keys(events) == []

    # Test timer finish after manual disable.
    motion_dimmer.timer_callback()
    events = mock_adapter.flush_entries()

    # Timer is updated to "idle".
    assert entry_keys(events) == ["track_timer"]

    # Disable the segment.
    mock_adapter.is_on = True
    mock_adapter.is_segment_enabled = False
    motion_dimmer.triggered_callback()
    motion_dimmer.predictor_callback()
    motion_dimmer.periodic_callback()
    events = mock_adapter.flush_entries()

    # Nothing happens.
    assert entry_keys(events) == []


async def test_temp_disable():
    """Test disable settings."""

    mock_adapter = MockAdapter()
    motion_dimmer = MotionDimmer(mock_adapter)

    # Test disable motion dimmer.
    mock_adapter.disabled_until = now() + timedelta(seconds=100)
    motion_dimmer.triggered_callback()
    motion_dimmer.predictor_callback()
    motion_dimmer.periodic_callback()
    events = mock_adapter.flush_entries()

    # Nothing happens.
    assert entry_keys(events) == []


async def test_cause_temp_disable():
    disable_events = [
        "dimmer_state_callback",
        "schedule_timer",
        "set_temporarily_disabled",
    ]

    mock_adapter = MockAdapter()
    motion_dimmer = MotionDimmer(mock_adapter)

    # Manually turn on the light while the triggers are off.
    mock_adapter._state_change = DimmerStateChange(False, True, 0, 255)
    motion_dimmer.dimmer_state_callback()
    events = mock_adapter.flush_entries()

    # Motion dimmer is temporarily disabled.
    assert entry_keys(events) == disable_events
    assert get_entry_value(events, "set_temporarily_disabled", "secs") == 600

    # Manually turn on the light while the triggers are on.
    mock_adapter._state_change = DimmerStateChange(False, True, 0, 255)
    mock_adapter.are_triggers_on = True
    motion_dimmer.dimmer_state_callback()
    events = mock_adapter.flush_entries()

    # Motion dimmer is NOT temporarily disabled.
    assert entry_keys(events) == [
        "dimmer_state_callback",
    ]

    # Manually turn off the light while the triggers are on.
    mock_adapter._state_change = DimmerStateChange(True, False, 255, 0)
    mock_adapter.are_triggers_on = True
    motion_dimmer.dimmer_state_callback()
    events = mock_adapter.flush_entries()

    # Motion dimmer is temporarily disabled.
    assert entry_keys(events) == disable_events

    # Manually change the brightness of the light.
    mock_adapter._state_change = DimmerStateChange(True, True, 255, 100)
    motion_dimmer.dimmer_state_callback()
    events = mock_adapter.flush_entries()

    # Motion dimmer is temporarily disabled.
    assert entry_keys(events) == disable_events

    # Manually change light but not brightness.
    mock_adapter._state_change = DimmerStateChange(True, True, 255, 255)
    motion_dimmer.dimmer_state_callback()
    events = mock_adapter.flush_entries()

    # Motion dimmer is NOT temporarily disabled.
    assert entry_keys(events) == [
        "dimmer_state_callback",
    ]

    # Manually change light while Motion Dimmer is disabled.
    mock_adapter._state_change = DimmerStateChange(False, True, 0, 255)
    mock_adapter.is_segment_enabled = False
    mock_adapter.are_triggers_on = False
    motion_dimmer.dimmer_state_callback()
    events = mock_adapter.flush_entries()

    # Nothing happens.
    assert entry_keys(events) == []


async def test_extension():
    """Test extending timer."""

    mock_adapter = MockAdapter()
    motion_dimmer = MotionDimmer(mock_adapter)

    # Set trigger and dimmer on and lower max so we don't have to repeat as much.
    mock_adapter.are_triggers_on = True
    mock_adapter.is_dimmer_on = True
    max_ext = 200
    mock_adapter.extension_max = max_ext

    old_secs = DEFAULT_SEG_SECONDS

    extension_events = [
        "turn_on_dimmer",
        "cancel_timer",
        "schedule_timer",
        "track_timer",
        "cancel_periodic_timer",
        "schedule_periodic_timer",
    ]
    with patch(
        "custom_components.motion_dimmer.models.MotionDimmer.dimmer_on_seconds",
        return_value=200,
        new_callable=PropertyMock,
    ):
        # Repeatedly callback to extend time.
        for i in range(4):
            motion_dimmer.periodic_callback()
            events = mock_adapter.flush_entries()
            assert entry_keys(events) == extension_events
            current_secs = get_entry_value(events, "schedule_timer", "secs")

            # Time keeps increasing.
            assert current_secs > old_secs
            old_secs = current_secs

        # Push it beyond the max.
        for i in range(4):
            motion_dimmer.periodic_callback()
            events = mock_adapter.flush_entries()
            assert entry_keys(events) == extension_events

            # Extension does not increase beyond max.
            assert (
                get_entry_value(events, "schedule_timer", "secs")
                == DEFAULT_SEG_SECONDS + max_ext
            )

    # Turn off the dimmer for a short time.
    mock_adapter.are_triggers_on = False
    mock_adapter.is_dimmer_on = False

    with patch(
        "custom_components.motion_dimmer.models.MotionDimmer.dimmer_off_seconds",
        return_value=SMALL_TIME_OFF - 1,
        new_callable=PropertyMock,
    ):
        motion_dimmer.triggered_callback()
        events = mock_adapter.flush_entries()

        # Extension has not changed.
        assert entry_keys(events) == TRIGGER_EVENTS
        assert (
            get_entry_value(events, "schedule_timer", "secs")
            == DEFAULT_SEG_SECONDS + max_ext
        )

    # Turn off dimmer for a medium time.
    with patch(
        "custom_components.motion_dimmer.models.MotionDimmer.dimmer_off_seconds",
        return_value=LONG_TIME_OFF - 1,
        new_callable=PropertyMock,
    ):
        motion_dimmer.triggered_callback()
        events = mock_adapter.flush_entries()

        # Extension has decreased but not completely.
        assert entry_keys(events) == TRIGGER_EVENTS
        assert get_entry_value(
            events, "schedule_timer", "secs"
        ) == DEFAULT_SEG_SECONDS + (max_ext / 2)

    # Turn off for a long time.
    with patch(
        "custom_components.motion_dimmer.models.MotionDimmer.dimmer_off_seconds",
        return_value=LONG_TIME_OFF + 1,
        new_callable=PropertyMock,
    ):
        motion_dimmer.triggered_callback()
        events = mock_adapter.flush_entries()

        # Extension has reset.
        assert entry_keys(events) == TRIGGER_EVENTS
        assert get_entry_value(events, "schedule_timer", "secs") == DEFAULT_SEG_SECONDS


async def test_periodic_timer():
    """Test periodic timer."""

    mock_adapter = MockAdapter()
    motion_dimmer = MotionDimmer(mock_adapter)

    # Periodic timer check when trigger is off.
    motion_dimmer.periodic_callback()
    events = mock_adapter.flush_entries()

    # Timer restarts but nothing else.
    assert entry_keys(events) == [
        "cancel_periodic_timer",
        "schedule_periodic_timer",
    ]

    # Set trigger interval to 0.
    mock_adapter.trigger_interval = 0

    # Interval might have changed in the middle of a period.
    motion_dimmer.periodic_callback()
    events = mock_adapter.flush_entries()

    # Nothing happens.
    assert entry_keys(events) == []

    # Trigger the motion dimmer.
    motion_dimmer.triggered_callback()
    events = mock_adapter.flush_entries()

    # Events fired but not periodic timer.
    assert entry_keys(events) == [
        "turn_on_dimmer",
        "cancel_timer",
        "schedule_timer",
        "track_timer",
        "turn_on_script",
    ]


async def test_init_timer():
    """Test initialize timer on restart."""

    mock_adapter = MockAdapter()
    motion_dimmer = MotionDimmer(mock_adapter)

    # No timers are running after restart.
    motion_dimmer.init_timer()
    events = mock_adapter.flush_entries()

    # Nothing is changed.
    assert entry_keys(events) == []

    # A timer scheduled for the future was running after restart.
    mock_adapter.timer = TimerState(
        now() + timedelta(seconds=10), "00:00:10", SENSOR_ACTIVE
    )
    motion_dimmer.init_timer()
    events = mock_adapter.flush_entries()

    # The timer is restarted.
    assert entry_keys(events) == [
        "cancel_timer",
        "schedule_timer",
        "track_timer",
    ]

    # A timer was active but is now in the past.
    mock_adapter.timer = TimerState(
        now() - timedelta(seconds=10), "00:00:10", SENSOR_ACTIVE
    )
    motion_dimmer.init_timer()
    events = mock_adapter.flush_entries()

    # Dimmer stopped after restart.
    assert entry_keys(events) == TURN_OFF_EVENTS

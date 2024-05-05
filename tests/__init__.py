"""Tests for Motion Dimmer integration."""

from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import Event, HomeAssistant
from homeassistant.setup import async_setup_component, logging
from homeassistant.util.dt import now, parse_duration
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.motion_dimmer.const import (
    DEFAULT_EXTENSION_MAX,
    DEFAULT_MIN_BRIGHTNESS,
    DEFAULT_PREDICTION_BRIGHTNESS,
    DEFAULT_PREDICTION_SECS,
    DEFAULT_SEG_SECONDS,
    DEFAULT_TRIGGER_INTERVAL,
    DOMAIN,
    SENSOR_IDLE,
    ControlEntities,
    ControlEntityData,
)
from custom_components.motion_dimmer.models import (
    MotionDimmerAdapter,
    TimerState,
    external_id,
)

from .const import (
    BINARY_SENSOR_DOMAIN,
    CONFIG_NAME,
    INPUT_SELECT_DOMAIN,
    LIGHT_DOMAIN,
    MOCK_BINARY_SENSOR_1_ID,
    MOCK_BINARY_SENSOR_2_ID,
    MOCK_BINARY_SENSORS,
    MOCK_CONFIG,
    MOCK_INPUT_SELECT,
    MOCK_LIGHT_1_ID,
    MOCK_LIGHTS,
    MOCK_OPTIONS,
    MOCK_SCRIPTS,
    SCRIPT_DOMAIN,
)

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR, force=True)


def event_log(events: list[Event]) -> Any:
    """Extract data from an event list."""
    for event in events:
        _LOGGER.warning(f"{event}")


def event_extract(events: list[Event], key: str, subkey: str | None = None) -> Any:
    """Extract data from an event list."""
    for event in events:
        value = dict(event.data).get(key)
        if value:
            if subkey:
                return dict(value).get(subkey)

            return value
    return None


def event_contains(events: list[Event], sub_dict) -> bool:
    """Check data from an event list."""
    for event in events:
        data = dict(event.data)
        if sub_dict.items() <= data.items():
            return True
    return False


async def setup_integration(
    hass: HomeAssistant,
    *,
    config=deepcopy(MOCK_CONFIG),
    options=deepcopy(MOCK_OPTIONS),
    # entry_id="1",
    unique_id=CONFIG_NAME,
    source=SOURCE_USER,
) -> MockConfigEntry:
    """Create the integration."""

    # Add required entities.
    await async_setup_component(hass, INPUT_SELECT_DOMAIN, MOCK_INPUT_SELECT)
    await hass.async_block_till_done()
    await async_setup_component(hass, LIGHT_DOMAIN, MOCK_LIGHTS)
    await hass.async_block_till_done()
    await async_setup_component(hass, BINARY_SENSOR_DOMAIN, MOCK_BINARY_SENSORS)
    await hass.async_block_till_done()
    await async_setup_component(hass, SCRIPT_DOMAIN, MOCK_SCRIPTS)
    await hass.async_block_till_done()

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=source,
        data=deepcopy(config),
        options=deepcopy(options),
        unique_id=unique_id,
    )
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    return config_entry


def get_disable_delta(hass: HomeAssistant) -> int:
    """Get the time difference between now and the temporary disable field."""
    disable_id = external_id(hass, ControlEntities.DISABLED_UNTIL, CONFIG_NAME)
    delta = datetime.fromisoformat(hass.states.get(disable_id).state) - now()
    return delta.total_seconds()


async def advance_time(hass: HomeAssistant, seconds, frozen_time):
    """Advance the system clock."""
    await hass.async_block_till_done()
    frozen_time.move_to(now() + timedelta(seconds=seconds))
    async_fire_time_changed(hass, now(), True)
    await hass.async_block_till_done()


async def set_segment_light_to(
    hass: HomeAssistant, segment, service, settings: dict | None = None
):
    """Set segment light to settings."""
    await hass.async_block_till_done()
    seg_1_light = external_id(hass, ControlEntities.SEG_LIGHT, CONFIG_NAME, segment)
    settings = settings or {}
    settings |= {"entity_id": seg_1_light}
    await hass.services.async_call(LIGHT_DOMAIN, service, settings, True)
    await hass.async_block_till_done()


def from_pct(num: float) -> float:
    """Convert 255 int to percent"""
    return round(num * 2.55, 2)


def to_pct(num: float) -> float:
    """Convert percent to 255 int"""
    return round(num / 2.55, 2)


async def dimmer_is_set_to(events: list[Event], values: dict):
    """Check that the dimmer is set to the desired value."""
    assert event_extract(events, "domain") == LIGHT_DOMAIN
    assert event_extract(events, "service") == "turn_on"
    assert event_extract(events, "service_data", "entity_id") == MOCK_LIGHT_1_ID
    for key, value in values.items():
        assert event_extract(events, "service_data", key) == value


async def dimmer_is_off(events: list):
    """Check that dimmer is off."""
    assert event_extract(events, "domain") == LIGHT_DOMAIN
    assert event_extract(events, "service") == "turn_off"
    assert event_extract(events, "service_data", "entity_id") == MOCK_LIGHT_1_ID


async def turn_off_trigger(hass, frozen_time):
    """Turn off the trigger."""
    await hass.async_block_till_done()
    hass.states.async_set(MOCK_BINARY_SENSOR_1_ID, "off")
    await advance_time(hass, 0.1, frozen_time)
    await hass.async_block_till_done()


async def let_dimmer_turn_off(hass, frozen_time):
    """Let the the dimmer turn off."""
    await turn_off_trigger(hass, frozen_time)
    await advance_time(hass, 60 * 60, frozen_time)
    await dimmer_is_not_temporarily_disabled(hass)


async def dimmer_is_not_temporarily_disabled(hass):
    """Check the disable time."""
    assert get_disable_delta(hass) <= 1


async def trigger_motion_dimmer(hass, frozen_time, prediction=False):
    """Trigger the motion dimmer."""
    await hass.async_block_till_done()
    binary_sensor = MOCK_BINARY_SENSOR_2_ID if prediction else MOCK_BINARY_SENSOR_1_ID
    hass.states.async_set(binary_sensor, "off")
    await advance_time(hass, 0.1, frozen_time)
    hass.states.async_set(binary_sensor, "on")
    await advance_time(hass, 0.1, frozen_time)


async def turn_on_segment(hass):
    """Set current segment to brightness 255."""
    await set_segment_light_to(hass, "seg_1", "turn_on", {ATTR_BRIGHTNESS: 255})
    await dimmer_is_not_temporarily_disabled(hass)


async def get_timer_duration(hass):
    """Get the current timer duration."""
    sensor = external_id(hass, ControlEntities.TIMER, CONFIG_NAME)
    duration = parse_duration(hass.states.get(sensor).attributes.get("duration"))
    return int(duration.total_seconds())


async def set_number_field_to(hass, field: ControlEntityData, value: Any, seg=None):
    """Set field value."""
    await hass.async_block_till_done()
    field_id = external_id(hass, field, CONFIG_NAME, seg)
    await hass.services.async_call(
        field.platform,
        "set_value",
        {"entity_id": field_id, "value": value},
        True,
    )
    await hass.async_block_till_done()


def get_field_state(hass, field: ControlEntityData, seg=None):
    """Get the field state."""
    field_id = external_id(hass, field, CONFIG_NAME, seg)
    return hass.states.get(field_id).state


async def call_service(hass, service, data):
    """Call a service."""
    await hass.services.async_call(
        DOMAIN,
        service,
        data,
        blocking=True,
    )
    await hass.async_block_till_done()


def secs(time: datetime):
    """Get number of seconds until a datetime."""
    return round((time - now()).total_seconds())


def dur(duration: str):
    """Get number of seconds from a duration string."""
    return round(parse_duration(duration).total_seconds())


def entry_keys(log: list[dict]) -> list:
    """Get a list of keys from the log."""
    keys = []
    for entry in log:
        keys.append(list(entry.keys())[0])
    return keys


def has_entry(log: list[dict], key) -> bool:
    """Check if log has entry based on key."""
    for entry in log:
        if entry.get(key):
            return True

    return False


def get_entry_value(log: list[dict], key, subkey) -> Any:
    """Return the value of a log entry based on key."""
    for entry in log:
        if entry.get(key) and entry.get(key).get(subkey):
            return entry.get(key).get(subkey)

    return None


class MockAdapter(MotionDimmerAdapter):
    """Mock adapter for testing."""

    # Override the properties so they can be set manually.
    are_triggers_on: bool = False
    brightness_min: int = 0
    disabled_until: datetime = now()
    extension_max: int = 0
    is_dimmer_on: bool = False
    is_segment_enabled: bool = False
    is_on: bool = False
    manual_override = 0
    prediction_brightness: int = 0
    prediction_secs: int = 0
    segment_id: str = ""
    trigger_interval: int = 0
    events: list = []
    brightness: int = 0
    color_mode: str = ""
    color_temp: int = 0
    rgb_color: tuple = ()
    seconds: int = 0
    timer: TimerState = None

    def __init__(self):
        # Initialize with the default values.
        self._log: list = []
        self.are_triggers_on = False
        self.brightness_min = DEFAULT_MIN_BRIGHTNESS
        self.disabled_until = now()
        self.extension_max = DEFAULT_EXTENSION_MAX
        self.is_dimmer_on = False
        self.is_segment_enabled = True
        self.is_on = True
        self.manual_override = 600
        self.prediction_brightness = DEFAULT_PREDICTION_BRIGHTNESS
        self.prediction_secs = DEFAULT_PREDICTION_SECS
        self.segment_id = "seg_1"
        self.trigger_interval = DEFAULT_TRIGGER_INTERVAL
        self.brightness = 255
        self.color_mode = ColorMode.WHITE
        self.color_temp = None
        self.rgb_color = None
        self.seconds = DEFAULT_SEG_SECONDS
        self.timer = TimerState(now(), "00:00:00", SENSOR_IDLE)
        self._state_change = None

    def flush_entries(self):
        """Return the entries and clear the log."""
        log = self._log
        self._log = []
        return log

    def cancel_periodic_timer(self) -> None:
        self._log.append({"cancel_periodic_timer": True})

    def cancel_timer(self) -> None:
        self._log.append({"cancel_timer": True})

    def dimmer_state_callback(self, *args, **kwargs) -> None:
        self._log.append({"dimmer_state_callback": kwargs})
        return self._state_change

    def schedule_periodic_timer(self, time, callback) -> None:
        self._log.append(
            {
                "schedule_periodic_timer": {
                    "secs": secs(time),
                    "call": callback.__name__,
                }
            }
        )

    def schedule_pump_timer(self, time, callback) -> None:
        self._log.append(
            {
                "schedule_pump_timer": {
                    "secs": secs(time),
                    "call": callback.__name__,
                }
            }
        )

    def schedule_timer(self, time: datetime, duration: str, callback) -> None:
        self._log.append(
            {
                "schedule_timer": {
                    "secs": secs(time),
                    "dur": dur(duration),
                    "call": callback.__name__,
                }
            }
        )

    def set_temporarily_disabled(self, next_time: datetime):
        self._log.append({"set_temporarily_disabled": {"secs": secs(next_time)}})

    def track_timer(self, timer_end, duration, state) -> None:
        self._log.append(
            {
                "track_timer": {
                    "secs": secs(timer_end),
                    "dur": dur(duration),
                    "state": state,
                }
            }
        )

    def turn_on_dimmer(self, **kwargs) -> None:
        self._log.append({"turn_on_dimmer": kwargs})

    def turn_off_dimmer(self) -> None:
        self._log.append({"turn_off_dimmer": True})

    def turn_on_script(self) -> None:
        self._log.append({"turn_on_script": True})

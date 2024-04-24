"""Tests for Motion Dimmer integration."""

from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import Event, HomeAssistant
from homeassistant.setup import async_setup_component, logging
from homeassistant.util.dt import now, parse_duration
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
    async_fire_time_changed,
)
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
)

from custom_components.motion_dimmer.const import (
    DOMAIN,
    ControlEntities,
    ControlEntityData,
)
from custom_components.motion_dimmer.models import external_id

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


logging.basicConfig(level=logging.ERROR, force=True)


_LOGGER = logging.getLogger(__name__)


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
    entry_id="1",
    unique_id=CONFIG_NAME,
    source=SOURCE_USER,
):
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
        entry_id=entry_id,
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
    async_fire_time_changed(hass, now())
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


async def dimmer_is_set_to(events: list, values: dict):
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


async def turn_off_trigger(hass):
    """Turn off the trigger."""
    await hass.async_block_till_done()
    hass.states.async_set(MOCK_BINARY_SENSOR_1_ID, "off")
    await hass.async_block_till_done()


async def let_dimmer_turn_off(hass, frozen_time):
    """Let the the dimmer turn off."""
    # await hass.async_block_till_done()
    # hass.states.async_set(MOCK_BINARY_SENSOR_1_ID, "off")
    # await hass.async_block_till_done()
    await turn_off_trigger(hass)
    events = async_capture_events(hass, "call_service")
    await advance_time(hass, 60 * 60 * 12, frozen_time)
    await hass.async_block_till_done()
    await dimmer_is_not_temporarily_disabled(hass)
    await dimmer_is_off(events)


async def dimmer_is_not_temporarily_disabled(hass):
    """Check the disable time."""
    assert get_disable_delta(hass) <= 1


async def trigger_motion_dimmer(hass, prediction=False):
    """Trigger the motion dimmer."""
    await hass.async_block_till_done()
    binary_sensor = MOCK_BINARY_SENSOR_2_ID if prediction else MOCK_BINARY_SENSOR_1_ID
    hass.states.async_set(binary_sensor, "off")
    await hass.async_block_till_done()
    events = async_capture_events(hass, "call_service")
    hass.states.async_set(binary_sensor, "on")
    await hass.async_block_till_done()
    return events


async def turn_on_segment(hass):
    """Set current segment to brightness 255."""
    await set_segment_light_to(hass, "seg_1", "turn_on", {ATTR_BRIGHTNESS: 255})
    await dimmer_is_not_temporarily_disabled(hass)


async def get_timer_duration(hass):
    """Get the current timer duration."""
    control_switch = external_id(hass, ControlEntities.CONTROL_SWITCH, CONFIG_NAME)
    duration = parse_duration(
        hass.states.get(control_switch).attributes.get("duration")
    )
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

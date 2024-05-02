"""Test Motion Dimmer setup process."""

import logging
from unittest.mock import patch, PropertyMock
from freezegun import freeze_time
from datetime import datetime, timedelta
from custom_components.motion_dimmer.models import (
    DimmerStateChange,
    MotionDimmer,
    MotionDimmerAdapter,
    MotionDimmerHA,
)
from homeassistant.util.dt import utcnow
from homeassistant.core import HomeAssistant
from homeassistant.components.datetime import DOMAIN as DATETIME_DOMAIN
from custom_components.motion_dimmer.const import (
    DEFAULT_EXTENSION_MAX,
    DEFAULT_MANUAL_OVERRIDE,
    DEFAULT_MIN_BRIGHTNESS,
    DEFAULT_PREDICTION_BRIGHTNESS,
    DEFAULT_PREDICTION_SECS,
    DEFAULT_SEG_SECONDS,
    DEFAULT_TRIGGER_INTERVAL,
    SMALL_TIME_OFF,
    LONG_TIME_OFF,
    ControlEntities,
    PUMP_TIME,
)

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_COLOR_TEMP,
    ATTR_RGB_COLOR,
    ATTR_WHITE,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)

from tests import (
    MockAdapter,
    advance_time,
    event_contains,
    event_extract,
    event_keys,
    from_pct,
    get_event_value,
    let_dimmer_turn_off,
    setup_integration,
    trigger_motion_dimmer,
    turn_on_segment,
)

from .const import (
    SCRIPT_DOMAIN,
    LIGHT_DOMAIN,
    MOCK_LIGHT_2_ID,
)
from homeassistant.util.dt import now, parse_duration

_LOGGER = logging.getLogger(__name__)

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
    async_fire_time_changed,
)


def dummy_callback():
    pass


async def test_home_assistant_adapter(hass: HomeAssistant):
    with freeze_time(utcnow()) as frozen_time:
        config_entry = await setup_integration(hass)
        adapter = MotionDimmerHA(hass, config_entry.entry_id)

        # Read defaults from Home Assistant
        assert adapter.are_triggers_on == False
        assert adapter.brightness == 255
        assert adapter.brightness_min == from_pct(DEFAULT_MIN_BRIGHTNESS)
        assert adapter.color_mode == ColorMode.WHITE
        assert adapter.color_temp == None
        assert adapter.rgb_color == None
        delta = (now() - adapter.disabled_until).total_seconds()
        assert -1 < delta < 1
        assert adapter.extension_max == DEFAULT_EXTENSION_MAX
        assert adapter.is_dimmer_on == False
        assert adapter.is_enabled
        assert adapter.is_on
        assert adapter.segment_id == "seg_1"
        assert adapter.prediction_brightness == from_pct(DEFAULT_PREDICTION_BRIGHTNESS)
        assert adapter.prediction_secs == DEFAULT_PREDICTION_SECS
        assert adapter.seconds == DEFAULT_SEG_SECONDS
        assert adapter.trigger_interval == DEFAULT_TRIGGER_INTERVAL

        events = async_capture_events(hass, "call_service")
        await adapter.async_set_temporarily_disabled(now())
        await hass.async_block_till_done()
        assert event_extract(events, "domain") == DATETIME_DOMAIN
        assert event_extract(events, "service") == "set_value"

        events.clear()
        await adapter.async_turn_on_dimmer()
        await hass.async_block_till_done()
        assert event_extract(events, "domain") == LIGHT_DOMAIN
        assert event_extract(events, "service") == "turn_on"

        events.clear()
        await adapter.async_turn_off_dimmer()
        await hass.async_block_till_done()
        assert event_extract(events, "domain") == LIGHT_DOMAIN
        assert event_extract(events, "service") == "turn_off"

        await advance_time(hass, 1000, frozen_time)

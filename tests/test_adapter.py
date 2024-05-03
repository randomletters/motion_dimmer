"""Test Motion Dimmer setup process."""

import logging

from freezegun import freeze_time
from homeassistant.components.datetime import DOMAIN as DATETIME_DOMAIN
from homeassistant.components.script import DOMAIN as SCRIPT_DOMAIN
from homeassistant.components.light import (
    ColorMode,
)
from homeassistant.core import HomeAssistant
from homeassistant.util.dt import now, utcnow

from pytest_homeassistant_custom_component.common import (
    async_capture_events,
)

from custom_components.motion_dimmer.const import (
    DEFAULT_EXTENSION_MAX,
    DEFAULT_MIN_BRIGHTNESS,
    DEFAULT_PREDICTION_BRIGHTNESS,
    DEFAULT_PREDICTION_SECS,
    DEFAULT_SEG_SECONDS,
    DEFAULT_TRIGGER_INTERVAL,
)
from custom_components.motion_dimmer.models import (
    MotionDimmerHA,
)
from tests import (
    advance_time,
    event_extract,
    from_pct,
    setup_integration,
)

from .const import (
    LIGHT_DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def test_home_assistant_adapter(hass: HomeAssistant):
    """Test the motion dimmer adapter for Home Assistant."""
    with freeze_time(utcnow()) as frozen_time:
        config_entry = await setup_integration(hass)
        adapter = MotionDimmerHA(hass, config_entry.entry_id)

        # Read defaults from Home Assistant
        assert adapter.are_triggers_on == False
        assert adapter.brightness == 255
        assert adapter.brightness_min == from_pct(DEFAULT_MIN_BRIGHTNESS)
        assert adapter.color_mode == ColorMode.WHITE
        assert adapter.color_temp is None
        assert adapter.rgb_color is None
        delta = (now() - adapter.disabled_until).total_seconds()
        assert -1 < delta < 1
        assert adapter.extension_max == DEFAULT_EXTENSION_MAX
        assert adapter.is_dimmer_on == False
        assert adapter.is_segment_enabled
        assert adapter.is_on
        assert adapter.manual_override == 600
        assert adapter.segment_id == "seg_1"
        assert adapter.prediction_brightness == from_pct(DEFAULT_PREDICTION_BRIGHTNESS)
        assert adapter.prediction_secs == DEFAULT_PREDICTION_SECS
        assert adapter.seconds == DEFAULT_SEG_SECONDS
        assert adapter.trigger_interval == DEFAULT_TRIGGER_INTERVAL
        timer = adapter.timer
        delta = (now() - timer.end_time).total_seconds()
        assert -1 < delta < 1
        assert timer.duration == "00:00:00"

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

        events.clear()
        await adapter.async_turn_on_script()
        await hass.async_block_till_done()
        assert event_extract(events, "domain") == SCRIPT_DOMAIN

        # Test having no script.
        events.clear()
        adapter.data.script = None
        await adapter.async_turn_on_script()
        await hass.async_block_till_done()
        assert event_extract(events, "domain") is None

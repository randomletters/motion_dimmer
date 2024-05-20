"""Test Motion Dimmer features."""

import logging
from freezegun import freeze_time
from homeassistant.util.dt import utcnow
from homeassistant.core import HomeAssistant
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
)
from pytest_homeassistant_custom_component.common import (
    async_capture_events,
)

from custom_components.motion_dimmer.const import (
    PUMP_TIME,
    ControlEntities,
)
from tests import (
    advance_time,
    dimmer_is_not_temporarily_disabled,
    dimmer_is_set_to,
    from_pct,
    get_disable_delta,
    let_dimmer_turn_off,
    set_number_field_to,
    set_segment_light_to,
    setup_integration,
    trigger_motion_dimmer,
)
from tests.const import LIGHT_DOMAIN, MOCK_LIGHT_1_ID


logging.basicConfig(level=logging.ERROR, force=True)
_LOGGER = logging.getLogger(__name__)


async def test_pump(hass: HomeAssistant):
    """Test the minimum brightness."""
    with freeze_time(utcnow()) as frozen_time:
        config_entry = await setup_integration(hass)
        events = async_capture_events(hass, "call_service")

        await set_number_field_to(hass, ControlEntities.TRIGGER_INTERVAL, 0)
        await set_number_field_to(hass, ControlEntities.SEG_SECONDS, 10, "seg_1")
        await set_number_field_to(hass, ControlEntities.EXTENSION_MAX, 0)

        # Set current segment to brightness 3.
        await set_segment_light_to(hass, "seg_1", "turn_on", {ATTR_BRIGHTNESS: 3})

        events.clear()
        await trigger_motion_dimmer(hass, frozen_time)

        # Dimmer is set to brightness 3.
        await dimmer_is_set_to(events, {ATTR_BRIGHTNESS: 3})
        await dimmer_is_not_temporarily_disabled(hass)
        await let_dimmer_turn_off(hass, frozen_time)

        # Set minimum brightness 10.
        current_min_pct = 10
        await set_number_field_to(hass, ControlEntities.MIN_BRIGHTNESS, current_min_pct)

        await dimmer_is_not_temporarily_disabled(hass)

        events.clear()
        await trigger_motion_dimmer(hass, frozen_time)

        await dimmer_is_not_temporarily_disabled(hass)

        # Dimmer is set to brightness %10.
        await dimmer_is_set_to(events, {ATTR_BRIGHTNESS: from_pct(current_min_pct)})

        events.clear()

        # Let the pump subside.
        await advance_time(hass, PUMP_TIME, frozen_time)

        # Dimmer is set to brightness 3.
        await dimmer_is_set_to(events, {ATTR_BRIGHTNESS: 3})

        # Motion dimmer is not temporarily disabled.
        await dimmer_is_not_temporarily_disabled(hass)

        # Set current segment to brightness above current minimum.
        above = current_min_pct + 10
        await set_segment_light_to(
            hass, "seg_1", "turn_on", {ATTR_BRIGHTNESS: from_pct(above)}
        )

        events.clear()
        await trigger_motion_dimmer(hass, frozen_time)

        # Dimmer is set to brightness above current minimum.
        await dimmer_is_set_to(events, {ATTR_BRIGHTNESS: from_pct(above)})
        await dimmer_is_not_temporarily_disabled(hass)

        events.clear()
        # # Finish timers.
        await let_dimmer_turn_off(hass, frozen_time)
        await dimmer_is_not_temporarily_disabled(hass)

        assert await config_entry.async_unload(hass)
        await hass.async_block_till_done()


async def test_callbacks(hass: HomeAssistant):
    """Test the minimum brightness."""
    with freeze_time(utcnow()) as frozen_time:
        config_entry = await setup_integration(hass)
        events = async_capture_events(hass, "call_service")

        await set_number_field_to(hass, ControlEntities.TRIGGER_INTERVAL, 0)
        await set_number_field_to(hass, ControlEntities.SEG_SECONDS, 10, "seg_1")
        await set_number_field_to(hass, ControlEntities.EXTENSION_MAX, 0)

        # Set current segment to brightness 50.
        await set_segment_light_to(hass, "seg_1", "turn_on", {ATTR_BRIGHTNESS: 50})
        await hass.async_block_till_done()

        events.clear()
        await trigger_motion_dimmer(hass, frozen_time)

        # Dimmer is set to brightness 50.
        await dimmer_is_set_to(events, {ATTR_BRIGHTNESS: 50})
        await dimmer_is_not_temporarily_disabled(hass)

        # Manually change light to brightness 100
        # (include color temp because of issue with light templates)
        await hass.services.async_call(
            LIGHT_DOMAIN,
            "turn_on",
            {"entity_id": MOCK_LIGHT_1_ID, ATTR_COLOR_TEMP: 500, ATTR_BRIGHTNESS: 100},
            True,
        )
        await hass.async_block_till_done()

        assert get_disable_delta(hass) > 598

        await let_dimmer_turn_off(hass, frozen_time)

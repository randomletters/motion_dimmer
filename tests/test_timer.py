"""Test Motion Dimmer setup process."""

import logging

from freezegun import freeze_time
from homeassistant.core import HomeAssistant
from homeassistant.util.dt import utcnow
from pytest_homeassistant_custom_component.common import (
    async_capture_events,
)

from custom_components.motion_dimmer.const import (
    ControlEntities,
)
from custom_components.motion_dimmer.models import external_id
from tests import (
    event_extract,
    get_field_state,
    get_timer_duration,
    let_dimmer_turn_off,
    set_number_field_to,
    setup_integration,
    advance_time,
    trigger_motion_dimmer,
    turn_on_segment,
)

from .const import (
    CONFIG_NAME,
    # MOCK_LIGHT_2_ID,
    LIGHT_DOMAIN,
    MOCK_LIGHT_1_ID,
    SMALL_TIME,
)

_LOGGER = logging.getLogger(__name__)


async def test_timers(hass: HomeAssistant):
    """Test the integration setup."""
    with freeze_time(utcnow()) as frozen_time:
        config_entry = await setup_integration(hass)

        # Capture events.
        events = async_capture_events(hass, "call_service")
        # Set current segment light to on.
        seg_1_light = external_id(hass, ControlEntities.SEG_LIGHT, CONFIG_NAME, "seg_1")
        hass.states.async_set(seg_1_light, "on")
        await hass.async_block_till_done()

        # Let time pass to prevent event overlap.
        await advance_time(hass, SMALL_TIME, frozen_time)

        await trigger_motion_dimmer(hass)

        # Dimmer is activated.
        assert event_extract(events, "domain") == LIGHT_DOMAIN
        assert event_extract(events, "service") == "turn_on"
        assert event_extract(events, "service_data", "entity_id") == MOCK_LIGHT_1_ID

        # Wait 10 seconds.
        await advance_time(hass, 10, frozen_time)

        # No events are fired.
        events = async_capture_events(hass, "call_service")
        assert event_extract(events, "domain") is None

        await let_dimmer_turn_off(hass, frozen_time)

        # Set segment to non default value.
        await turn_on_segment(hass)
        await set_number_field_to(hass, ControlEntities.SEG_SECONDS, 200, "seg_1")

        events = async_capture_events(hass, "call_service")
        await trigger_motion_dimmer(hass)

        # Timer is active and has a duration.
        assert await get_timer_duration(hass) > 0
        assert get_field_state(hass, ControlEntities.TIMER) == "active"

        # Reload Home Assistant.
        assert await config_entry.async_unload(hass)
        await setup_integration(hass)

        # Timer is restored and active.
        assert await get_timer_duration(hass) > 0
        assert get_field_state(hass, ControlEntities.TIMER) == "active"

        await let_dimmer_turn_off(hass, frozen_time)

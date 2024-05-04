"""Test Motion Dimmer timer."""

import logging

from freezegun import freeze_time
from homeassistant.core import HomeAssistant
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.util.dt import utcnow

from custom_components.motion_dimmer.const import (
    ControlEntities,
)
from tests import (
    get_field_state,
    get_timer_duration,
    let_dimmer_turn_off,
    set_number_field_to,
    setup_integration,
    advance_time,
    trigger_motion_dimmer,
)


_LOGGER = logging.getLogger(__name__)


async def test_timers(hass: HomeAssistant):
    """Test the integration setup."""
    with freeze_time(utcnow()) as frozen_time:
        config_entry = await setup_integration(hass)

        await set_number_field_to(hass, ControlEntities.TRIGGER_INTERVAL, 0)
        await set_number_field_to(hass, ControlEntities.SEG_SECONDS, 10, "seg_1")
        await set_number_field_to(hass, ControlEntities.EXTENSION_MAX, 0)

        await trigger_motion_dimmer(hass, frozen_time)

        # Timer is active and has a duration.
        assert await get_timer_duration(hass) > 0
        assert get_field_state(hass, ControlEntities.TIMER) == "active"

        # Reload Home Assistant.
        assert await config_entry.async_unload(hass)
        await hass.async_block_till_done()
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        # Initialize any timers that were running before shutdown.
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)

        await advance_time(hass, 5, frozen_time)

        # Timer is restored and active.
        assert await get_timer_duration(hass) > 0
        assert get_field_state(hass, ControlEntities.TIMER) == "active"

        await let_dimmer_turn_off(hass, frozen_time)

        # Reload Home Assistant.
        assert await config_entry.async_unload(hass)
        await hass.async_block_till_done()
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        await advance_time(hass, 5, frozen_time)

        # Timer is restored and idle.
        assert await get_timer_duration(hass) <= 1
        assert get_field_state(hass, ControlEntities.TIMER) == "idle"

        await let_dimmer_turn_off(hass, frozen_time)

        # assert await config_entry.async_unload(hass)
        # await hass.async_block_till_done()

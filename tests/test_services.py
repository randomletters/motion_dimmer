"""Test Motion Dimmer setup process."""

import logging

from freezegun import freeze_time
from homeassistant.core import HomeAssistant
from homeassistant.util.dt import utcnow
from homeassistant.helpers import entity_registry as er

from custom_components.motion_dimmer.const import (
    DEFAULT_MANUAL_OVERRIDE,
    SENSOR_DURATION,
    SENSOR_END_TIME,
    SERVICE_DISABLE,
    SERVICE_ENABLE,
    SERVICE_FINISH_TIMER,
    SERVICE_HOURS,
    ControlEntities,
)
from custom_components.motion_dimmer.models import external_id
from tests import (
    get_disable_delta,
    setup_integration,
    turn_off_trigger,
    turn_on_segment,
    trigger_motion_dimmer,
    get_timer_duration,
    call_service,
)

from .const import (
    CONFIG_NAME,
)


_LOGGER = logging.getLogger(__name__)


async def test_services(hass: HomeAssistant):
    """Test the integration setup."""
    with freeze_time(utcnow()) as frozen_time:
        config_entry = await setup_integration(hass)

        # Fire the disable_until service with no time specified.
        disable_id = external_id(hass, ControlEntities.DISABLED_UNTIL, CONFIG_NAME)
        await call_service(hass, SERVICE_DISABLE, {"entity_id": disable_id})

        # Motion dimmer is temporarily disabled for the default time (with buffer).
        assert round(get_disable_delta(hass)) > DEFAULT_MANUAL_OVERRIDE - 5

        # Fire the disable_until service with time specified.
        disable_id = external_id(hass, ControlEntities.DISABLED_UNTIL, CONFIG_NAME)
        await call_service(
            hass,
            SERVICE_DISABLE,
            {"entity_id": disable_id, SERVICE_HOURS: 1},
        )

        # Motion dimmer is temporarily disabled for about an hour.
        assert round(get_disable_delta(hass)) > (60 * 60) - 5

        # Get the device id from one of the entities.
        entity_reg = er.async_get(hass)
        entries = er.async_entries_for_config_entry(entity_reg, config_entry.entry_id)
        device_id = entries[0].device_id

        # Call the enable service (using device id for coverage).
        await call_service(hass, SERVICE_ENABLE, {"device_id": device_id})

        # Motion dimmer is no longer disabled.
        assert get_disable_delta(hass) < 1

        switch_id = external_id(hass, ControlEntities.CONTROL_SWITCH, CONFIG_NAME)
        attr = hass.states.get(switch_id).attributes
        assert attr.get(SENSOR_END_TIME) is None
        assert attr.get(SENSOR_DURATION) is None

        # Trigger dimmer and make sure the timer is running.
        await turn_on_segment(hass)
        await trigger_motion_dimmer(hass, frozen_time)
        await turn_off_trigger(hass, frozen_time)
        assert await get_timer_duration(hass) > 0

        # Call the finish_timer service.
        timer_id = external_id(hass, ControlEntities.TIMER, CONFIG_NAME)
        await call_service(hass, SERVICE_FINISH_TIMER, {"entity_id": timer_id})

        # Timer is no longer running.
        assert await get_timer_duration(hass) <= 1

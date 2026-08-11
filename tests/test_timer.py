"""Test Motion Dimmer timer."""

from datetime import timedelta
import logging

from freezegun import freeze_time
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant
from homeassistant.helpers import restore_state
from homeassistant.util.dt import utcnow, now
from custom_components.motion_dimmer.const import (
    SENSOR_ACTIVE,
    SENSOR_DURATION,
    SENSOR_END_TIME,
    ControlEntities,
)
from tests import (
    advance_time,
    get_field_state,
    get_timer_duration,
    let_dimmer_turn_off,
    set_number_field_to,
    setup_integration,
    setup_last_state,
    trigger_motion_dimmer,
)

_LOGGER = logging.getLogger(__name__)


async def test_load_active_timer(hass: HomeAssistant):
    """Test loading an active timer."""
    timer_id = "sensor.test_config_timer"

    setup_last_state(
        hass,
        {
            "entity_id": timer_id,
            "state": "on",
            "attributes": {
                SENSOR_END_TIME: now() + timedelta(seconds=15),
                SENSOR_DURATION: 60,
            },
        },
    )

    config_entry = await setup_integration(hass)

    assert hass.states.get(timer_id).attributes.get(SENSOR_DURATION) == 60


async def test_load_expired_timer(hass: HomeAssistant):
    """Test loading an expired timer."""
    timer_id = "sensor.test_config_timer"

    setup_last_state(
        hass,
        {
            "entity_id": timer_id,
            "state": "on",
            "attributes": {
                SENSOR_END_TIME: now() + timedelta(seconds=-15),
                SENSOR_DURATION: 60,
            },
        },
    )

    config_entry = await setup_integration(hass)

    assert hass.states.get(timer_id).attributes.get(SENSOR_DURATION) == 60

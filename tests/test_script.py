"""Test Motion Dimmer setup process."""

import logging
from freezegun import freeze_time
from homeassistant.util.dt import utcnow
from homeassistant.core import HomeAssistant

from tests import (
    event_contains,
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

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR, force=True)


async def test_script(hass: HomeAssistant):
    """Test changing light settings."""
    with freeze_time(utcnow()) as frozen_time:
        await setup_integration(hass)
        await turn_on_segment(hass)

        events = await trigger_motion_dimmer(hass)

        # Script is activated and works.
        assert event_contains(events, {"domain": SCRIPT_DOMAIN})
        assert event_contains(
            events,
            {
                "domain": LIGHT_DOMAIN,
                "service": "turn_on",
                "service_data": {"entity_id": MOCK_LIGHT_2_ID},
            },
        )

        events = await trigger_motion_dimmer(hass)

        # Script is not activated when dimmer is active.
        assert not event_contains(events, {"domain": SCRIPT_DOMAIN})

        await let_dimmer_turn_off(hass, frozen_time)

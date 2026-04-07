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

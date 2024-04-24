"""Test Motion Dimmer setup process."""

import logging
from freezegun import freeze_time
from homeassistant.util.dt import utcnow
from homeassistant.core import HomeAssistant
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_RGB_COLOR,
    ATTR_TRANSITION,
    ATTR_WHITE,
)

from custom_components.motion_dimmer.const import (
    DEFAULT_SEG_SECONDS,
    ControlEntities,
)
from custom_components.motion_dimmer.models import external_id
from tests import (
    advance_time,
    dimmer_is_set_to,
    let_dimmer_turn_off,
    set_segment_light_to,
    setup_integration,
    event_extract,
    trigger_motion_dimmer,
)

from .const import (
    CONFIG_NAME,
    MOCK_BINARY_SENSOR_1_ID,
    SWITCH_DOMAIN,
)

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR, force=True)


async def test_light_settings(hass: HomeAssistant):
    """Test changing light settings."""
    with freeze_time(utcnow()) as frozen_time:
        await setup_integration(hass)

        # Set current segment to brightness 50.
        await set_segment_light_to(hass, "seg_1", "turn_on", {ATTR_BRIGHTNESS: 50})

        events = await trigger_motion_dimmer(hass)

        # Dimmer is set to brightness 50.
        await dimmer_is_set_to(
            events,
            {
                ATTR_BRIGHTNESS: 50,
                ATTR_TRANSITION: 1,
                ATTR_RGB_COLOR: None,
                ATTR_COLOR_TEMP: None,
            },
        )

        # Set current segment to brightness 80, red.
        await set_segment_light_to(
            hass,
            "seg_1",
            "turn_on",
            {ATTR_BRIGHTNESS: 80, ATTR_RGB_COLOR: (255, 0, 0)},
        )

        events = await trigger_motion_dimmer(hass)

        # Dimmer is set to brightness 80, red.
        await dimmer_is_set_to(
            events,
            {
                ATTR_BRIGHTNESS: 80,
                ATTR_TRANSITION: 1,
                ATTR_RGB_COLOR: (255, 0, 0),
                ATTR_COLOR_TEMP: None,
            },
        )

        # Set current segment to brightness 90, 3500K.
        await set_segment_light_to(
            hass, "seg_1", "turn_on", {ATTR_BRIGHTNESS: 90, ATTR_COLOR_TEMP: 3508}
        )

        events = await trigger_motion_dimmer(hass)

        # Dimmer is set to brightness 90, 3508K.
        await dimmer_is_set_to(
            events,
            {
                ATTR_BRIGHTNESS: 90,
                ATTR_TRANSITION: 1,
                ATTR_RGB_COLOR: None,
                ATTR_COLOR_TEMP: 3508,
            },
        )

        # Set current segment to white.
        await set_segment_light_to(hass, "seg_1", "turn_on", {ATTR_WHITE: True})

        events = await trigger_motion_dimmer(hass)

        # Dimmer has no color information.
        await dimmer_is_set_to(
            events,
            {
                ATTR_RGB_COLOR: None,
                ATTR_COLOR_TEMP: None,
            },
        )

        # Let the the dimmer turn off.
        await let_dimmer_turn_off(hass, frozen_time)

        # Turn off the motion dimmer.
        control_switch = external_id(hass, ControlEntities.CONTROL_SWITCH, CONFIG_NAME)
        await hass.services.async_call(
            SWITCH_DOMAIN, "turn_off", {"entity_id": control_switch}, True
        )

        events = await trigger_motion_dimmer(hass)

        # Dimmer is still off.
        assert event_extract(events, "domain") is None

        # Turn on the motion dimmer.
        control_switch = external_id(hass, ControlEntities.CONTROL_SWITCH, CONFIG_NAME)
        await hass.services.async_call(
            SWITCH_DOMAIN, "turn_on", {"entity_id": control_switch}, True
        )

        # Turn off the current segment.
        await set_segment_light_to(hass, "seg_1", "turn_off")

        events = await trigger_motion_dimmer(hass)

        # Dimmer is still off.
        assert event_extract(events, "domain") is None

        # Finish timers.
        hass.states.async_set(MOCK_BINARY_SENSOR_1_ID, "off")
        await advance_time(hass, DEFAULT_SEG_SECONDS, frozen_time)

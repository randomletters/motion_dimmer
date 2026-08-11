"""Test Motion Dimmer light."""

import json
import logging

from freezegun import freeze_time
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_RGB_COLOR,
    ATTR_TRANSITION,
    ATTR_WHITE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import restore_state
from homeassistant.util.dt import utcnow
from pytest_homeassistant_custom_component.common import (
    JSONEncoder,
    async_capture_events,
)

from custom_components.motion_dimmer.const import (
    DEFAULT_SEG_SECONDS,
    ControlEntities,
)
from custom_components.motion_dimmer.models import external_id, internal_id
from tests import (
    advance_time,
    dimmer_is_set_to,
    event_extract,
    let_dimmer_turn_off,
    set_segment_light_to,
    setup_integration,
    setup_last_state,
    trigger_motion_dimmer,
)

from .const import (
    CONFIG_NAME,
    LIGHT_DOMAIN,
    MOCK_BINARY_SENSOR_1_ID,
    SWITCH_DOMAIN,
)

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR, force=True)


async def test_light_settings(hass: HomeAssistant):
    """Test changing light settings."""
    with freeze_time(utcnow(), real_asyncio=True) as frozen_time:
        config_entry = await setup_integration(hass)

        # Set current segment to brightness 50.
        await set_segment_light_to(hass, "seg_1", "turn_on", {ATTR_BRIGHTNESS: 50})

        events = async_capture_events(hass, "call_service")
        await trigger_motion_dimmer(hass, frozen_time)

        # Dimmer is set to brightness 50.
        await dimmer_is_set_to(
            events,
            {
                ATTR_BRIGHTNESS: 50,
                ATTR_TRANSITION: 1,
                ATTR_RGB_COLOR: None,
                ATTR_COLOR_TEMP_KELVIN: None,
            },
        )

        # Set current segment to brightness 80, red.
        await set_segment_light_to(
            hass,
            "seg_1",
            "turn_on",
            {ATTR_BRIGHTNESS: 80, ATTR_RGB_COLOR: (255, 0, 0)},
        )

        events.clear()
        await trigger_motion_dimmer(hass, frozen_time)

        # Dimmer is set to brightness 80, red.
        await dimmer_is_set_to(
            events,
            {
                ATTR_BRIGHTNESS: 80,
                ATTR_TRANSITION: 1,
                ATTR_RGB_COLOR: (255, 0, 0),
                ATTR_COLOR_TEMP_KELVIN: None,
            },
        )

        # Set current segment to brightness 90, 3500K.
        await set_segment_light_to(
            hass,
            "seg_1",
            "turn_on",
            {ATTR_BRIGHTNESS: 90, ATTR_COLOR_TEMP_KELVIN: 3508},
        )

        events.clear()
        await trigger_motion_dimmer(hass, frozen_time)

        # Dimmer is set to brightness 90, 3508K.
        await dimmer_is_set_to(
            events,
            {
                ATTR_BRIGHTNESS: 90,
                ATTR_TRANSITION: 1,
                ATTR_RGB_COLOR: None,
                ATTR_COLOR_TEMP_KELVIN: 3508,
            },
        )

        # Set current segment to white.
        await set_segment_light_to(hass, "seg_1", "turn_on", {ATTR_WHITE: True})

        events.clear()
        await trigger_motion_dimmer(hass, frozen_time)

        # Dimmer has no color information.
        await dimmer_is_set_to(
            events,
            {
                ATTR_RGB_COLOR: None,
                ATTR_COLOR_TEMP_KELVIN: None,
            },
        )

        # Let the the dimmer turn off.
        await let_dimmer_turn_off(hass, frozen_time)

        # Turn off the motion dimmer.
        control_switch = external_id(hass, ControlEntities.CONTROL_SWITCH, CONFIG_NAME)
        await hass.services.async_call(
            SWITCH_DOMAIN, "turn_off", {"entity_id": control_switch}, True
        )

        events.clear()
        await trigger_motion_dimmer(hass, frozen_time)

        # Dimmer is still off.
        assert event_extract(events, "domain") is None

        # Turn on the motion dimmer.
        control_switch = external_id(hass, ControlEntities.CONTROL_SWITCH, CONFIG_NAME)
        await hass.services.async_call(
            SWITCH_DOMAIN, "turn_on", {"entity_id": control_switch}, True
        )

        # Turn off the current segment.
        await set_segment_light_to(hass, "seg_1", "turn_off")

        events.clear()
        await trigger_motion_dimmer(hass, frozen_time)

        # Dimmer is still off.
        assert event_extract(events, "domain") is None

        # Finish timers.
        hass.states.async_set(MOCK_BINARY_SENSOR_1_ID, "off")
        await advance_time(hass, DEFAULT_SEG_SECONDS, frozen_time)

        await hass.async_block_till_done()


async def test_load_state(hass: HomeAssistant):
    """Test loading entity settings."""

    seg_1_light = "light.test_config_option_seg_1"
    setup_last_state(
        hass,
        {
            "entity_id": seg_1_light,
            "state": "on",
            "attributes": {
                ATTR_BRIGHTNESS: 50,
                ATTR_COLOR_MODE: "color_temp",
                ATTR_COLOR_TEMP_KELVIN: 3508,
                ATTR_RGB_COLOR: None,
            },
        },
    )

    config_entry = await setup_integration(hass)

    assert hass.states.get(seg_1_light).attributes.get(ATTR_BRIGHTNESS) == 50

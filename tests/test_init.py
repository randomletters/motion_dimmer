"""Test Motion Dimmer setup process."""

import logging
from homeassistant.core import HomeAssistant

from custom_components.motion_dimmer.const import (
    DEFAULT_EXTENSION_MAX,
    DEFAULT_MANUAL_OVERRIDE,
    DEFAULT_MIN_BRIGHTNESS,
    DEFAULT_PREDICTION_BRIGHTNESS,
    DEFAULT_PREDICTION_SECS,
    DEFAULT_SEG_SECONDS,
    DEFAULT_TRIGGER_INTERVAL,
    ControlEntities,
)
from custom_components.motion_dimmer.models import external_id, segments
from tests import (
    get_disable_delta,
    setup_integration,
)

from .const import (
    CONFIG_NAME,
)

_LOGGER = logging.getLogger(__name__)


async def test_setup(hass: HomeAssistant):
    """Test the integration setup."""
    config_entry = await setup_integration(hass)
    # Default settings are set correctly.
    assert segments(hass, config_entry) == {"seg_1": "Seg 1", "seg_2": "Seg 2"}
    entity_id = external_id(hass, ControlEntities.CONTROL_SWITCH, CONFIG_NAME)
    assert hass.states.get(entity_id).state == "on"
    entity_id = external_id(hass, ControlEntities.EXTENSION_MAX, CONFIG_NAME)
    assert hass.states.get(entity_id).state == str(DEFAULT_EXTENSION_MAX)
    entity_id = external_id(hass, ControlEntities.MANUAL_OVERRIDE, CONFIG_NAME)
    assert hass.states.get(entity_id).state == str(DEFAULT_MANUAL_OVERRIDE)
    entity_id = external_id(hass, ControlEntities.MIN_BRIGHTNESS, CONFIG_NAME)
    assert hass.states.get(entity_id).state == str(DEFAULT_MIN_BRIGHTNESS)
    entity_id = external_id(hass, ControlEntities.PREDICTION_BRIGHTNESS, CONFIG_NAME)
    assert hass.states.get(entity_id).state == str(DEFAULT_PREDICTION_BRIGHTNESS)
    entity_id = external_id(hass, ControlEntities.PREDICTION_SECS, CONFIG_NAME)
    assert hass.states.get(entity_id).state == str(DEFAULT_PREDICTION_SECS)
    entity_id = external_id(hass, ControlEntities.SEG_LIGHT, CONFIG_NAME, "seg_1")
    assert hass.states.get(entity_id).state == "off"
    entity_id = external_id(hass, ControlEntities.SEG_SECONDS, CONFIG_NAME, "seg_1")
    assert hass.states.get(entity_id).state == str(DEFAULT_SEG_SECONDS)
    entity_id = external_id(hass, ControlEntities.SEG_LIGHT, CONFIG_NAME, "seg_2")
    assert hass.states.get(entity_id).state == "off"
    entity_id = external_id(hass, ControlEntities.SEG_SECONDS, CONFIG_NAME, "seg_2")
    assert hass.states.get(entity_id).state == str(DEFAULT_SEG_SECONDS)
    entity_id = external_id(hass, ControlEntities.TRIGGER_INTERVAL, CONFIG_NAME)
    assert hass.states.get(entity_id).state == str(DEFAULT_TRIGGER_INTERVAL)
    entity_id = external_id(hass, ControlEntities.CONTROL_SWITCH, CONFIG_NAME)
    assert hass.states.get(entity_id).state == "on"
    entity_id = external_id(hass, ControlEntities.DISABLED_UNTIL, CONFIG_NAME)
    assert get_disable_delta(hass) <= 1

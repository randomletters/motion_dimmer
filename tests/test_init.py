"""Test Motion Dimmer setup process."""

import logging
from copy import deepcopy
from datetime import timedelta
from homeassistant.util.dt import utcnow
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.motion_dimmer.const import DOMAIN, ControlEntities
from custom_components.motion_dimmer.models import external_id, segments

from .const import (
    CONFIG_NAME,
    MOCK_CONFIG,
    MOCK_INPUT_SELECT,
    MOCK_OPTIONS,
    MOCK_LIGHTS,
    MOCK_BINARY_SENSORS,
    INPUT_SELECT_DOMAIN,
    BINARY_SENSOR_DOMAIN,
    LIGHT_DOMAIN,
)

CONF_ID = "12345"

_LOGGER = logging.getLogger(__name__)


async def setup_integration(
    hass: HomeAssistant,
    *,
    config=MOCK_CONFIG,
    options=MOCK_OPTIONS,
    entry_id="1",
    unique_id=CONF_ID,
    source=SOURCE_USER,
):
    """Create the integration."""

    await async_setup_component(hass, INPUT_SELECT_DOMAIN, MOCK_INPUT_SELECT)
    await hass.async_block_till_done()
    await async_setup_component(hass, LIGHT_DOMAIN, MOCK_LIGHTS)
    await hass.async_block_till_done()
    await async_setup_component(hass, BINARY_SENSOR_DOMAIN, MOCK_BINARY_SENSORS)
    await hass.async_block_till_done()

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=source,
        data=deepcopy(config),
        options=deepcopy(options),
        entry_id=entry_id,
        unique_id=unique_id,
    )
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    return config_entry


async def test_setup(hass: HomeAssistant):
    """Test the integration setup."""
    config_entry = await setup_integration(hass)
    assert segments(hass, config_entry) == {"seg_1": "Seg 1", "seg_2": "Seg 2"}
    entity_id = external_id(hass, ControlEntities.MIN_BRIGHTNESS, CONFIG_NAME)
    assert hass.states.get(entity_id).state == "1"
    assert hass.states.get("light.test_light_1").state == "off"
    assert hass.states.get("binary_sensor.test_binary_sensor_1").state == "off"
    assert hass.states.get("switch.test_config_motion_dimmer").state == "on"

    hass.states.async_set("light.test_config_option_seg_1", "on")
    await hass.async_block_till_done()
    hass.states.async_set("binary_sensor.test_binary_sensor_1", "on")
    await hass.async_block_till_done()
    assert hass.states.get("light.test_config_option_seg_1").state == "on"
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    assert hass.states.get("light.test_light_1").state == "on"
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=60))
    assert hass.states.get("light.test_light_1").state == "off"

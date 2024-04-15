"""Test Motion Dimmer setup process."""

import logging
from copy import deepcopy

import pytest
from homeassistant.components.input_select import DOMAIN as INPUT_SELECT_DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.motion_dimmer.const import DOMAIN, ControlEntities
from custom_components.motion_dimmer.models import external_id, segments

from .const import CONFIG_NAME, MOCK_CONFIG, MOCK_INPUT_SELECT, MOCK_OPTIONS

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
    test = await setup_integration(hass)
    assert segments(hass, test) == {"seg_1": "Seg 1", "seg_2": "Seg 2"}
    entity_id = external_id(hass, ControlEntities.MIN_BRIGHTNESS, CONFIG_NAME)
    assert hass.states.get(entity_id).state == "1"

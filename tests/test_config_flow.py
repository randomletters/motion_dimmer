"""Test the config flow."""

import logging

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from custom_components.motion_dimmer.const import (
    DOMAIN,
)
from tests import setup_integration
from tests.const import MOCK_CONFIG, MOCK_OPTIONS

_LOGGER = logging.getLogger(__name__)


async def test_form(hass):  # , connect):
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}

    # with MOCK_CONFIG as mock_setup_entry:
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG
    )
    await hass.async_block_till_done()

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["data"] == MOCK_CONFIG


async def test_options(hass: HomeAssistant) -> None:
    """Test options flow."""

    config_entry = await setup_integration(hass, options={})

    optionflow = await hass.config_entries.options.async_init(config_entry.entry_id)

    configured = await hass.config_entries.options.async_configure(
        optionflow["flow_id"], user_input=MOCK_OPTIONS
    )

    assert configured.get("type") is FlowResultType.CREATE_ENTRY
    assert config_entry.options == MOCK_OPTIONS

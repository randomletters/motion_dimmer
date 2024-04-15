"""Test the SmartThinQ sensors config flow."""

import logging

from homeassistant import config_entries, data_entry_flow

from custom_components.motion_dimmer.const import (
    DOMAIN,
)
from tests.const import MOCK_CONFIG

_LOGGER = logging.getLogger(__name__)


async def test_form(hass):  # , connect):
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}

    # with PATCH_SETUP_ENTRY as mock_setup_entry:
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG
    )
    await hass.async_block_till_done()

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["data"] == MOCK_CONFIG

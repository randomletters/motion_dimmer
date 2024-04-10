"""Config flow for Motion Dimmers integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.input_select import DOMAIN as INPUT_SELECT_DOMAIN
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.script import DOMAIN as SCRIPT_DOMAIN
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig

from .const import (
    CONF_DIMMER,
    CONF_FRIENDLY_NAME,
    CONF_INPUT_SELECT,
    CONF_PREDICTERS,
    CONF_SCRIPT,
    CONF_TRIGGERS,
    CONF_UNIQUE_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_UNIQUE_NAME): str,
        vol.Required(CONF_FRIENDLY_NAME): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    return {"title": data[CONF_FRIENDLY_NAME]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Motion Dimmers."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await validate_input(self.hass, user_input)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_FRIENDLY_NAME], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle the flow of options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.input = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""

        if user_input is not None:
            return self.async_create_entry(data=user_input)

        entry = self.config_entry

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_DIMMER,
                        default=entry.options.get(CONF_DIMMER, vol.UNDEFINED),
                    ): EntitySelector(
                        EntitySelectorConfig(
                            domain=[LIGHT_DOMAIN],
                            multiple=False,
                        ),
                    ),
                    vol.Required(
                        CONF_INPUT_SELECT,
                        default=entry.options.get(CONF_INPUT_SELECT, vol.UNDEFINED),
                    ): EntitySelector(
                        EntitySelectorConfig(
                            domain=[INPUT_SELECT_DOMAIN],
                            multiple=False,
                        ),
                    ),
                    vol.Optional(
                        CONF_TRIGGERS,
                        default=entry.options.get(CONF_TRIGGERS, vol.UNDEFINED),
                    ): EntitySelector(
                        EntitySelectorConfig(
                            domain=[BINARY_SENSOR_DOMAIN],
                            multiple=True,
                        ),
                    ),
                    vol.Optional(
                        CONF_PREDICTERS,
                        default=entry.options.get(CONF_PREDICTERS, vol.UNDEFINED),
                    ): EntitySelector(
                        EntitySelectorConfig(
                            domain=[BINARY_SENSOR_DOMAIN],
                            multiple=True,
                        ),
                    ),
                    vol.Optional(
                        CONF_SCRIPT,
                        default=entry.options.get(CONF_SCRIPT, vol.UNDEFINED),
                    ): EntitySelector(
                        EntitySelectorConfig(
                            domain=[SCRIPT_DOMAIN],
                            multiple=False,
                        ),
                    ),
                }
            ),
        )

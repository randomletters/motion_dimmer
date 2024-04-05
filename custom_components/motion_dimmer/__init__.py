"""The Motion Dimmers integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_DIMMER,
    CONF_FRIENDLY_NAME,
    CONF_INPUT_SELECT,
    CONF_PREDICTERS,
    CONF_TRIGGERS,
    CONF_UNIQUE_NAME,
    DOMAIN,
    SERVICE_DISABLE,
)
from .models import MotionDimmerData
from .services import async_service_temporarily_disable

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.DATETIME,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Handle the setup tasks."""

    async def async_temporarily_disable(call: ServiceCall):
        await async_service_temporarily_disable(hass, call)

    hass.services.async_register(DOMAIN, SERVICE_DISABLE, async_temporarily_disable)

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up Motion Dimmers from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = MotionDimmerData(
        device_id=entry.data[CONF_UNIQUE_NAME],
        device_name=entry.data[CONF_FRIENDLY_NAME],
        dimmer=entry.options.get(CONF_DIMMER, None),
        input_select=entry.options.get(CONF_INPUT_SELECT, None),
        triggers=entry.options.get(CONF_TRIGGERS, None),
        predicters=entry.options.get(CONF_PREDICTERS, None),
    )

    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def update_listener(hass: HomeAssistant, entry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

"""Platform for switch integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util.dt import now

from .const import (
    DOMAIN,
    SENSOR_DURATION,
    SENSOR_END_TIME,
    ControlEntities as CE,
)
from .models import MotionDimmerData, MotionDimmerEntity, internal_id

_LOGGER = logging.getLogger(__name__)


class MotionDimmerSwitch(MotionDimmerEntity, SwitchEntity, RestoreEntity):
    """Representation of a Motion Dimmer Switch."""

    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, data: MotionDimmerData, entity_name, unique_id) -> None:
        """Initialize the switch."""
        super().__init__(data, entity_name, unique_id)
        self._default_value = "on"
        self._data = data

    async def async_added_to_hass(self) -> None:
        """Restore last state."""
        last_state = await self.async_get_last_state()
        if last_state:
            self._attr_state = (
                last_state.state if last_state.state else self._default_value
            )
        else:
            self._attr_state = "on"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        self._attr_state = "on"
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        self._attr_state = "off"
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self._attr_state == "on"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor entry."""

    data: MotionDimmerData = hass.data[DOMAIN][entry.entry_id]

    switch = MotionDimmerSwitch(
        data,
        entity_name="Motion Dimmer",
        unique_id=internal_id(CE.CONTROL_SWITCH, data.device_id),
    )
    async_add_entities([switch])

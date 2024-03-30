"""Platform for datetime integration."""
from __future__ import annotations

import datetime
import logging

from homeassistant.components.datetime import DateTimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util.dt import now

from .const import DOMAIN, ControlEntities
from .models import MotionDimmerData, MotionDimmerEntity, internal_id

_LOGGER = logging.getLogger(__name__)


class MotionDimmerDateTime(MotionDimmerEntity, DateTimeEntity, RestoreEntity):
    """Representation of a DateTime."""

    _attr_name = None
    # _attr_should_poll = False

    def __init__(
        self,
        data: MotionDimmerData,
        entity_name,
        unique_id,
    ) -> None:
        """Initialize the date/time entity."""
        super().__init__(data, entity_name, unique_id)

        self._attr_native_value = now()

    async def async_set_value(self, value: datetime) -> None:
        """Update the date/time."""
        self._attr_native_value = value
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Restore last state."""
        last_state = await self.async_get_last_state()
        if last_state:
            self._attr_native_value = datetime.datetime.fromisoformat(
                str(last_state.state)
            )
        else:
            self._attr_native_value = now()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the datetime entry."""

    data: MotionDimmerData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            MotionDimmerDateTime(
                data,
                entity_name="Disabled Until",
                unique_id=internal_id(
                    ControlEntities.DISABLED_UNTIL,
                    data.device_id,
                ),
            ),
        ]
    )

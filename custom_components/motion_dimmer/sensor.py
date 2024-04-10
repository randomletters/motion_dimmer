"""Platform for sensor integration."""

from __future__ import annotations

import datetime
import logging

from homeassistant.components.sensor import RestoreSensor
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.dt import now

from .const import (
    DOMAIN,
    SENSOR_ACTIVE,
    SENSOR_DURATION,
    SENSOR_END_TIME,
    SENSOR_IDLE,
    ControlEntities,
)
from .models import MotionDimmerData, MotionDimmerEntity, internal_id

_LOGGER = logging.getLogger(__name__)


class TimerSensor(MotionDimmerEntity, RestoreSensor):
    """Representation of a Sensor."""

    _attr_device_class = None
    _attr_icon = "mdi:timer"

    def __init__(
        self,
        data: MotionDimmerData,
        entity_name,
        unique_id,
    ) -> None:
        """Initialize the Sensor."""
        super().__init__(data, entity_name, unique_id)

        self._attr_extra_state_attributes = {
            SENSOR_END_TIME: None,
            SENSOR_DURATION: None,
        }

    async def async_update(self) -> None:
        """Fetch new state data for the sensor."""

        switch_attrs = self.hass.states.get(
            self.external_id(ControlEntities.CONTROL_SWITCH)
        ).attributes
        timer_end = switch_attrs.get(SENSOR_END_TIME)
        timer_seconds = switch_attrs.get(SENSOR_DURATION)
        if timer_end:
            timer_end = datetime.datetime.fromisoformat(str(timer_end))
            self._attr_extra_state_attributes[SENSOR_END_TIME] = timer_end
            if timer_end > now():
                self._attr_native_value = SENSOR_ACTIVE
            else:
                self._attr_native_value = SENSOR_IDLE

            self._attr_extra_state_attributes[SENSOR_DURATION] = timer_seconds


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor entry."""

    data: MotionDimmerData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            TimerSensor(
                data,
                entity_name="Timer",
                unique_id=internal_id(ControlEntities.TIMER, data.device_id),
            ),
        ]
    )

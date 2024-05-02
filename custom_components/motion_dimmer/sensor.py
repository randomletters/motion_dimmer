"""Platform for sensor integration."""

from __future__ import annotations

from datetime import datetime
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
        timer_end = self._data.motion_dimmer.end_time
        timer_duration = self._data.motion_dimmer.duration
        if timer_end:
            self._attr_extra_state_attributes[SENSOR_END_TIME] = str(timer_end)
            if timer_end > now():
                self._attr_native_value = SENSOR_ACTIVE
            else:
                self._attr_native_value = SENSOR_IDLE

            self._attr_extra_state_attributes[SENSOR_DURATION] = timer_duration

    async def async_added_to_hass(self) -> None:
        """Restore last state."""
        last_state = await self.async_get_last_state()
        if last_state:
            timer_end = last_state.attributes.get(SENSOR_END_TIME)
            if timer_end:
                timer_end_dt = datetime.fromisoformat(
                    last_state.attributes.get(SENSOR_END_TIME)
                )
                timer_duration = last_state.attributes.get(SENSOR_DURATION)
                self._attr_extra_state_attributes[SENSOR_END_TIME] = timer_end
                self._attr_extra_state_attributes[SENSOR_DURATION] = timer_duration

                if timer_end_dt > now():
                    self._attr_native_value = SENSOR_ACTIVE
                else:
                    self._attr_native_value = SENSOR_IDLE


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

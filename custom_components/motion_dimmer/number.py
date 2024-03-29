"""Platform for number integration."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberDeviceClass, NumberMode, RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, ControlEntities
from .models import MotionDimmerData, MotionDimmerEntity, internal_id, segments

_LOGGER = logging.getLogger(__name__)


class MotionDimmerNumber(MotionDimmerEntity, RestoreNumber):
    """Representation of a Number."""

    _attr_has_entity_name = True

    def __init__(
        self,
        data: MotionDimmerData,
        entity_name,
        entity_id,
        default_value=None,
        min_value: float = 0,
    ) -> None:
        super().__init__(data, entity_name, entity_id)
        self._default_value = default_value
        self._attr_native_min_value = min_value

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        self._attr_native_value = int(value)
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Restore last state."""
        last_number_data = await self.async_get_last_number_data()
        value = (
            last_number_data.native_value
            if last_number_data is not None
            else self._default_value
        )
        self._attr_native_value = value


class PercentNumber(MotionDimmerNumber):
    """Representation of a Number."""

    _attr_native_max_value: float = 100
    _attr_native_min_value: float = 0
    _attr_native_step: float = 1
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = "%"


class TimeNumber(MotionDimmerNumber):
    """Representation of a Number."""

    _attr_native_max_value: float = 60 * 60 * 24 * 7
    _attr_native_step: float = 1
    _attr_mode = NumberMode.BOX
    _attr_device_class = NumberDeviceClass.DURATION
    _attr_native_unit_of_measurement = "sec"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor entry."""

    data: MotionDimmerData = hass.data[DOMAIN][entry.entry_id]

    entities = [
        PercentNumber(
            data,
            entity_name="Min. Brightness",
            entity_id=internal_id(ControlEntities.MIN_BRIGHTNESS, data.device_id),
            default_value=1,
        ),
        TimeNumber(
            data,
            entity_name="Trigger Test Interval",
            entity_id=internal_id(ControlEntities.TRIGGER_INTERVAL, data.device_id),
            default_value=60,
        ),
        TimeNumber(
            data,
            entity_name="Max. Extension",
            entity_id=internal_id(ControlEntities.EXTENSION_MAX, data.device_id),
            default_value=60 * 60,
            min_value=1,
        ),
        TimeNumber(
            data,
            entity_name="Manual Override Time",
            entity_id=internal_id(ControlEntities.MANUAL_OVERRIDE, data.device_id),
            default_value=60 * 10,
            min_value=0,
        ),
    ]

    if data.predicters:
        entities.append(
            TimeNumber(
                data,
                entity_name="Prediction Time",
                entity_id=internal_id(ControlEntities.PREDICTION_SECS, data.device_id),
                default_value=10,
                min_value=1,
            )
        )
        entities.append(
            PercentNumber(
                data,
                entity_name="Prediction Brightness",
                entity_id=internal_id(
                    ControlEntities.PREDICTION_BRIGHTNESS, data.device_id
                ),
                default_value=50,
            )
        )

    segs = segments(hass, entry)

    for seg_id, seg_name in segs.items():
        entities.append(
            TimeNumber(
                data,
                entity_name=f"-{seg_name} Seconds",
                entity_id=internal_id(
                    ControlEntities.SEG_SECONDS, data.device_id, seg_id
                ),
                default_value=60,
                min_value=1,
            )
        )

    async_add_entities(entities)

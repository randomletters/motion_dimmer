"""The motion_dimmer integration models."""

from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.util import slugify

from .const import DOMAIN, ControlEntityData

_LOGGER = logging.getLogger(__name__)


@dataclass
class MotionDimmerData:
    """Data for the motion_dimmer integration."""

    device_id: dict[str, Any]
    device_name: dict[str, Any]
    dimmer: dict[str, Any]
    input_select: dict[str, Any]
    triggers: dict[str, Any]
    predicters: dict[str, Any]


class MotionDimmerEntity(Entity):
    """Motion Dimmer entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        data: MotionDimmerData,
        entity_name: str,
        unique_id: str = None,
        entity_id: str = None,
    ) -> None:
        """Set up the base class."""
        self._data = data
        self._attr_name = entity_name
        self._attr_unique_id = unique_id if unique_id else entity_id
        if entity_id:
            self.entity_id = entity_id

        device_id = data.device_id
        self._device = device_id

        info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=data.device_name,
            manufacturer="Motion Dimmer",
            model="Motion Dimmer",
        )
        self._attr_device_info = info

    def external_id(
        self, ced: ControlEntityData, seg_id: str | None = None
    ) -> str | None:
        """Get the entity id from entity data."""
        return external_id(self.hass, ced, self._data.device_id, seg_id)


def segments(hass: HomeAssistant, entry: ConfigEntry) -> dict:
    """Get the segments from the input select."""
    segs = {}
    data: MotionDimmerData = hass.data[DOMAIN][entry.entry_id]

    if data.input_select:
        input_segments = hass.states.get(data.input_select).attributes["options"]

        for input_segment in input_segments:
            segs[slugify(input_segment)] = input_segment

    return segs


def internal_id(
    ced: ControlEntityData, device_id: str, seg_id: str | None = None
) -> str:
    """Create a unique id from parts."""
    suffix = seg_id + "_" + ced.id_suffix if seg_id else ced.id_suffix
    return ced.platform + "." + DOMAIN + "_" + device_id + "_" + suffix


def external_id(
    hass: HomeAssistant,
    ced: ControlEntityData,
    device_id: str,
    seg_id: str | None = None,
) -> str | None:
    """Get the entity id from entity data."""
    ent_reg = er.async_get(hass)
    if entity_id := ent_reg.async_get_entity_id(
        ced.platform, DOMAIN, internal_id(ced, device_id, seg_id)
    ):
        return entity_id

"""Motion Dimmer Light."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_COLOR_TEMP,
    ATTR_RGB_COLOR,
    ATTR_WHITE,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, ControlEntities
from .models import MotionDimmerData, MotionDimmerEntity, internal_id, segments

_LOGGER = logging.getLogger(__name__)


class MotionDimmerLight(MotionDimmerEntity, LightEntity, RestoreEntity):
    """Representation of a Motion Dimmer light."""

    _attr_brightness: int | None = None
    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = [ColorMode.COLOR_TEMP, ColorMode.RGB, ColorMode.WHITE]
    _attr_supported_features = LightEntityFeature(LightEntityFeature.TRANSITION)

    def turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""

        self._attr_is_on = True
        self._attr_state = "on"
        self._attr_brightness = kwargs.get(ATTR_BRIGHTNESS, self._attr_brightness)
        if kwargs.get(ATTR_RGB_COLOR):
            self._attr_color_mode = ColorMode.RGB
            self._attr_rgb_color = kwargs.get(ATTR_RGB_COLOR, self._attr_rgb_color)
        if kwargs.get(ATTR_COLOR_TEMP):
            self._attr_color_mode = ColorMode.COLOR_TEMP
            self._attr_color_temp = kwargs.get(ATTR_COLOR_TEMP, self._attr_color_temp)
        if kwargs.get(ATTR_WHITE):
            self._attr_color_mode = ColorMode.WHITE
            self._attr_color_temp = None
            self._attr_rgb_color = None

    def turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        self._attr_is_on = False
        self._attr_state = "off"

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self._attr_is_on

    async def async_added_to_hass(self) -> None:
        """Restore last state."""
        last_state = await self.async_get_last_state()
        self._attr_state = "off" if last_state is None else last_state.state
        self._attr_is_on = self._attr_state == "on"
        if last_state:
            self._attr_color_mode = last_state.attributes.get(ATTR_COLOR_MODE)
            self._attr_brightness = last_state.attributes.get(ATTR_BRIGHTNESS)
            self._attr_rgb_color = last_state.attributes.get(ATTR_RGB_COLOR)
            self._attr_color_temp = last_state.attributes.get(ATTR_COLOR_TEMP)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Abode light devices."""
    data: MotionDimmerData = hass.data[DOMAIN][entry.entry_id]

    segs = segments(hass, entry)
    entities = []

    for seg_id, seg_name in segs.items():
        entities.append(
            MotionDimmerLight(
                data,
                entity_name=f"-{seg_name} Light Settings",
                unique_id=internal_id(
                    ControlEntities.SEG_LIGHT, data.device_id, seg_id
                ),
            )
        )

    async_add_entities(entities)

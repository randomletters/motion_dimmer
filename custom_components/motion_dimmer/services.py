"""The Motion Dimmers services."""

import datetime
import logging

from homeassistant.components.datetime import DOMAIN as DATETIME_DOMAIN
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.service import ServiceTargetSelector
from homeassistant.util.dt import now

from .const import (
    DOMAIN,
    SERVICE_HOURS,
    SERVICE_MINUTES,
    SERVICE_SECONDS,
    ControlEntities as CE,
)
from .models import MotionDimmerData, external_id

_LOGGER = logging.getLogger(__name__)


async def async_service_temporarily_disable(hass: HomeAssistant, call: ServiceCall):
    """Handle the service call."""

    target = ServiceTargetSelector(call)
    if not target.has_any_selector:
        return

    entity_reg = er.async_get(hass)

    for unique_id in target.device_ids:
        entries = er.async_entries_for_device(entity_reg, unique_id)
        data: MotionDimmerData = hass.data[DOMAIN][entries[0].config_entry_id]
        await async_update_disable(hass, data, call)

    for entity_id in target.entity_ids:
        entity = entity_reg.async_get(entity_id)
        data: MotionDimmerData = hass.data[DOMAIN][entity.config_entry_id]
        await async_update_disable(hass, data, call)


async def async_update_disable(
    hass: HomeAssistant, data: MotionDimmerData, call: ServiceCall
):
    """Update the temporary disable entity."""

    seconds = int(call.data.get(SERVICE_SECONDS, 0))
    minutes = int(call.data.get(SERVICE_MINUTES, 0))
    hours = int(call.data.get(SERVICE_HOURS, 0))
    if seconds == 0 and minutes == 0 and hours == 0:
        seconds = int(
            hass.states.get(external_id(hass, CE.MANUAL_OVERRIDE, data.device_id)).state
        )
    else:
        seconds = seconds + (60 * minutes) + (60 * 60 * hours)

    if seconds > 0:
        delay = datetime.timedelta(seconds=seconds)
        next_time = now() + delay

        await hass.services.async_call(
            DATETIME_DOMAIN,
            "set_value",
            {
                "entity_id": external_id(hass, CE.DISABLED_UNTIL, data.device_id),
                "datetime": next_time,
            },
        )

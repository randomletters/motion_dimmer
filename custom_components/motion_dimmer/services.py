"""The Motion Dimmers services."""

import datetime
import logging

from homeassistant.components.datetime import DOMAIN as DATETIME_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
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
from .switch import MotionDimmerSwitch

_LOGGER = logging.getLogger(__name__)


async def async_service_temporarily_disable(hass: HomeAssistant, call: ServiceCall):
    """Handle the service call."""

    for data in get_data(hass, call).values():
        seconds = int(call.data.get(SERVICE_SECONDS, 0))
        minutes = int(call.data.get(SERVICE_MINUTES, 0))
        hours = int(call.data.get(SERVICE_HOURS, 0))
        if seconds == 0 and minutes == 0 and hours == 0:
            seconds = int(
                hass.states.get(
                    external_id(hass, CE.MANUAL_OVERRIDE, data.device_id)
                ).state
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


async def async_service_enable(hass: HomeAssistant, call: ServiceCall):
    """Handle the service call."""

    for data in get_data(hass, call).values():
        next_time = now()

        await hass.services.async_call(
            DATETIME_DOMAIN,
            "set_value",
            {
                "entity_id": external_id(hass, CE.DISABLED_UNTIL, data.device_id),
                "datetime": next_time,
            },
        )

        await hass.services.async_call(
            SWITCH_DOMAIN,
            "turn_on",
            {
                "entity_id": external_id(hass, CE.CONTROL_SWITCH, data.device_id),
            },
        )


async def async_service_finish_timer(hass: HomeAssistant, call: ServiceCall):
    """Handle the service call."""

    for data in get_data(hass, call).values():
        switch: MotionDimmerSwitch = data.switch_object
        await switch.async_schedule_callback()
        switch.cancel_periodic_timer()
        switch.cancel_timer()


def get_data(hass: HomeAssistant, call: ServiceCall) -> dict[str, MotionDimmerData]:
    """Get the ids from the call."""

    target = ServiceTargetSelector(call)
    if not target.has_any_selector:
        return

    data: dict[str, MotionDimmerData] = {}
    entity_reg = er.async_get(hass)
    for unique_id in target.device_ids:
        entries = er.async_entries_for_device(entity_reg, unique_id)
        data[entries[0].config_entry_id] = hass.data[DOMAIN][entries[0].config_entry_id]

    for entity_id in target.entity_ids:
        entity = entity_reg.async_get(entity_id)
        data[entity.config_entry_id] = hass.data[DOMAIN][entity.config_entry_id]

    return data

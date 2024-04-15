"""Platform for switch integration."""

from __future__ import annotations

import datetime
import logging
from typing import Any

from homeassistant.components.datetime import DOMAIN as DATETIME_DOMAIN
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_RGB_COLOR,
    ATTR_TRANSITION,
    DOMAIN as LIGHT_DOMAIN,
)
from homeassistant.components.script import DOMAIN as SCRIPT_DOMAIN
from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, ATTR_FRIENDLY_NAME, ATTR_ICON
from homeassistant.core import HassJob, HomeAssistant, State
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_point_in_time,
    async_track_state_change,
)
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import slugify
from homeassistant.util.dt import now

from .const import (
    DOMAIN,
    SENSOR_ACTIVE,
    SENSOR_DURATION,
    SENSOR_END_TIME,
    SENSOR_IDLE,
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
        self._is_prediction = False
        self._is_pump = False
        self._cancel_timer = None
        self._cancel_periodic_timer = None
        self._dimmer_previous_state = None
        self._additional_time = 0
        self._dimmer_time_on = now()
        self._dimmer_time_off = now()

        self._attr_extra_state_attributes = {
            SENSOR_END_TIME: None,
            SENSOR_DURATION: None,
        }

    async def async_added_to_hass(self) -> None:
        """Restore last state."""
        last_state = await self.async_get_last_state()
        if last_state:
            self._attr_state = (
                last_state.state if last_state.state else self._default_value
            )
            self._attr_extra_state_attributes[SENSOR_END_TIME] = (
                last_state.attributes.get(SENSOR_END_TIME)
            )
            self._attr_extra_state_attributes[SENSOR_DURATION] = (
                last_state.attributes.get(SENSOR_DURATION)
            )
            self.init_timer()
        else:
            self._attr_state = "on"

        # Add dimmer on listener
        if self._data.dimmer:
            async_track_state_change(
                self.hass,
                self._data.dimmer,
                self.async_dimmer_state_callback,
            )

        # Add trigger on listener
        if self._data.triggers:
            async_track_state_change(
                self.hass,
                self._data.triggers,
                self.async_trigger_on_callback,
                to_state="on",
            )

        # Add predicter on listener
        if self._data.predicters:
            async_track_state_change(
                self.hass,
                self._data.predicters,
                self.async_predicter_on_callback,
                to_state="on",
            )

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

    @property
    def are_triggers_on(self) -> bool:
        """True if any of the triggers are on."""
        for trigger in self._data.triggers:
            if self.hass.states.get(trigger).state == "on":
                return True

        return False

    @property
    def segment_id(self) -> str:
        """The unique id of the segment."""
        segment = self.hass.states.get(self._data.input_select).state
        return slugify(segment)

    @property
    def disabled_until(self) -> datetime:
        """The datetime when the motion dimmer is no longer disabled."""
        state = self.hass.states.get(self.external_id(CE.DISABLED_UNTIL))
        if state:
            try:
                return datetime.datetime.fromisoformat(str(state.state))
            except ValueError:
                return now()

    @property
    def brightness(self) -> float:
        """The brightness to set the dimmer to."""
        if self.is_enabled:
            entity_id = self.external_id(CE.SEG_LIGHT, self.segment_id)
            target = self.hass.states.get(entity_id).attributes.get(ATTR_BRIGHTNESS)

            if self._is_prediction:
                # Make sure it is brighter than min.
                new_target = max(self.prediction_brightness, self.brightness_min)

                # And less than regular brightness.
                return min(new_target, target)
            else:
                return target
        else:
            return 0

    @property
    def is_enabled(self) -> bool:
        """Return true if device is enabled."""
        if not self.is_on:
            return False

        if self.is_temporarily_disabled:
            return False

        return self.is_segment_enabled

    @property
    def is_temporarily_disabled(self) -> bool:
        """Return true if device is temporarily disabled."""
        return now() < self.disabled_until

    @property
    def is_segment_enabled(self) -> bool:
        """Return true if segment is enabled."""
        state = self.hass.states.get(self.external_id(CE.SEG_LIGHT, self.segment_id))
        if state:
            return state.state == "on"

        return False

    @property
    def seg_attrs(self) -> dict[str, Any]:
        """The light setting attributes."""
        values = {ATTR_TRANSITION: 1}
        if self.brightness:
            values[ATTR_BRIGHTNESS] = self.brightness
        if self.color_temp:
            values[ATTR_COLOR_TEMP] = self.color_temp
        elif self.rgb_color:
            values[ATTR_RGB_COLOR] = self.rgb_color

        return values

    @property
    def seconds(self) -> float:
        """Number of seconds to turn the dimmer on."""
        if self._is_prediction:
            return float(self.prediction_secs)
        else:
            entity_id = self.external_id(CE.SEG_SECONDS, self.segment_id)
            state = self.hass.states.get(entity_id)
            if state:
                return float(state.state) + self.additional_time

    @property
    def rgb_color(self) -> Any:
        """The color to set the dimmer to."""
        return self.hass.states.get(
            self.external_id(CE.SEG_LIGHT, self.segment_id)
        ).attributes.get(ATTR_RGB_COLOR)

    @property
    def color_temp(self) -> Any:
        """The color temp to set the dimmer to."""
        return self.hass.states.get(
            self.external_id(CE.SEG_LIGHT, self.segment_id)
        ).attributes.get(ATTR_COLOR_TEMP)

    @property
    def trigger_interval(self) -> float:
        """Number of seconds to wait before checking the triggers again."""
        entity_id = self.external_id(CE.TRIGGER_INTERVAL)
        return float(self.hass.states.get(entity_id).state)

    @property
    def extension_max(self) -> float:
        """Maximum number of seconds the timer can be extended."""
        entity_id = self.external_id(CE.EXTENSION_MAX)
        return float(self.hass.states.get(entity_id).state)

    @property
    def prediction_brightness(self) -> float:
        """The brightness of the predictive activation."""
        if not self._data.predicters:
            return 0
        entity_id = self.external_id(CE.PREDICTION_BRIGHTNESS)
        return float(self.hass.states.get(entity_id).state) * 255 / 100

    @property
    def prediction_secs(self) -> float:
        """The number of seconds to activate a prediction."""
        if not self._data.predicters:
            return 0
        entity_id = self.external_id(CE.PREDICTION_SECS)
        return float(self.hass.states.get(entity_id).state)

    @property
    def brightness_min(self) -> float:
        """The minimum brightness needed to activate the dimmer."""
        entity_id = self.external_id(CE.MIN_BRIGHTNESS)
        return float(self.hass.states.get(entity_id).state) * 255 / 100

    @property
    def dimmer_state(self) -> Any:
        """The state of the dimmer."""
        dimmer = self.hass.states.get(self._data.dimmer)
        if dimmer:
            return dimmer.state

    @property
    def is_dimmer_on(self) -> bool:
        """Is the dimmer currently on."""
        if self._is_prediction:
            return False
        else:
            return self.dimmer_state == "on"

    @property
    def dimmer_on_seconds(self) -> int:
        """Number of seconds the dimmer was on."""
        start_dt = self._dimmer_time_on
        end_dt = now()
        diff = end_dt - start_dt
        return round(diff.total_seconds())

    @property
    def dimmer_off_seconds(self) -> int:
        """Number of seconds the dimmer was off."""
        if self.is_dimmer_on:
            return 0

        start_dt = self._dimmer_time_off
        end_dt = now()
        diff = end_dt - start_dt
        return round(diff.total_seconds())

    @property
    def additional_time(self) -> int:
        """Amount of time to add to the timer."""
        if self._is_prediction:
            return 0

        # Initialize the attribute.
        self._additional_time = getattr(self, "_additional_time", 0)
        total = self._additional_time
        off_seconds = self.dimmer_off_seconds
        if off_seconds <= 0:
            # Light is on so only extend a small amount.
            total += int(self.dimmer_on_seconds / 5)
        elif off_seconds < 20:
            # Light was briefly off, so extend by normal amount
            total += self.dimmer_on_seconds
        elif off_seconds < (60 * 20):
            # Light was off for a little while, so decrease the extension.
            total -= int(self._additional_time / 2)
        else:
            # Light was off for long time.  Reset extension.
            total = 0

        # Make sure it is between 0 and max time.
        total = min(self.extension_max, max(total, 0))

        return total

    async def async_start_dimmer(self) -> None:
        """Turn on the dimmer."""
        if self.is_enabled:
            self._dimmer_previous_state = self.dimmer_state

            # _LOGGER.warning(f"Info: {self.seg_attrs}")

            if (
                not self._is_pump
                and not self._is_prediction
                and self._dimmer_previous_state == "off"
                and self.brightness
                and self.brightness < self.brightness_min
            ):
                self._is_pump = True
                self.reset_dimmer_time_on()
                attrs = self.seg_attrs
                attrs[ATTR_BRIGHTNESS] = self.brightness_min
                await self.async_turn_on_dimmer(attrs)
                self.schedule_pump_timer()
            else:
                self._is_pump = False
                await self.async_turn_on_dimmer(self.seg_attrs)

                if self._dimmer_previous_state == "off":
                    self.reset_dimmer_time_on()

                self.add_time()
                self.schedule_timer()
                self.schedule_periodic_timer()
                if self._dimmer_previous_state == "off":
                    await self.async_turn_on_script()

    async def async_stop_dimmer(self) -> None:
        """Turn off the dimmer."""
        if self.is_on and not self.is_temporarily_disabled:
            # Check if triggers are are still on and make sure the segment
            # didn't get disabled or transitioned to a disabled segment.
            if self.are_triggers_on and self.is_segment_enabled:
                # Restart everything instead of stopping.
                await self.async_start_dimmer()
            else:
                self._is_prediction = False
                self.cancel_timer()
                self.cancel_periodic_timer()
                await self.hass.services.async_call(
                    LIGHT_DOMAIN,
                    "turn_off",
                    {ATTR_ENTITY_ID: self._data.dimmer},
                )
                self.reset_dimmer_time_off()

    async def async_dimmer_state_callback(
        self,
        changed_entity: str,
        old_state: State | None,
        new_state: State | None,
    ) -> None:
        """Check if dimmer was changed manually."""
        if not self.is_enabled:
            return
        # Compare states.

        state = old_state.state == new_state.state
        brightness = old_state.attributes.get(
            ATTR_BRIGHTNESS
        ) == new_state.attributes.get(ATTR_BRIGHTNESS)

        # Don't worry about changes in color or temp.

        if not state:
            if (
                new_state.state == "on"
                and not self._is_prediction
                and not self.are_triggers_on
            ):
                await self.async_disable_temporarily()
            if new_state.state == "off" and self.are_triggers_on:
                await self.async_disable_temporarily()
        elif not brightness and not self._is_pump:
            new_bright = int(new_state.attributes.get(ATTR_BRIGHTNESS))
            # Give a 1 percent margin of error.
            if new_bright + 1 < self.brightness or new_bright - 1 > self.brightness:
                await self.async_disable_temporarily()

    async def async_disable_temporarily(self) -> None:
        """Disable all functionality for a time."""
        seconds = self.hass.states.get(self.external_id(CE.MANUAL_OVERRIDE)).state
        if seconds and int(seconds) > 0:
            delay = datetime.timedelta(seconds=int(seconds))
            next_time = now() + delay
        else:
            return

        # Only set a new disable if it is later than the old one.
        if self.disabled_until < next_time:
            # Schedule the timer to turn off dimmer after it is reenabled.
            buffer = datetime.timedelta(seconds=5)
            self.schedule_timer(next_time + buffer, str(int(seconds) + 5))
            await self.hass.services.async_call(
                DATETIME_DOMAIN,
                "set_value",
                {
                    "entity_id": self.external_id(CE.DISABLED_UNTIL),
                    "datetime": next_time,
                },
            )

    async def async_trigger_on_callback(
        self,
        changed_entity: str,
        old_state: State | None,
        new_state: State | None,
    ) -> None:
        """Run when triggers are activated."""
        self._is_prediction = False
        await self.async_start_dimmer()

    async def async_predicter_on_callback(
        self,
        changed_entity: str,
        old_state: State | None,
        new_state: State | None,
    ) -> None:
        """Register a callback for when predicters are activated."""
        if self.is_dimmer_on:
            return

        self._is_prediction = True
        await self.async_start_dimmer()

    async def async_pump_callback(self, *args: Any) -> None:
        """Turn on the dimmer to normal brightness after pump."""
        self._is_prediction = False
        await self.async_start_dimmer()

    async def async_check_triggers(self) -> None:
        """Restart dimmer if triggers are active."""
        if self.are_triggers_on:
            await self.async_start_dimmer()
        else:
            self.schedule_periodic_timer()

    async def async_schedule_callback(self, *args: Any) -> None:
        """Turn off the dimmer because timer ran out."""
        await self.async_stop_dimmer()
        self.track_timer()

    async def async_periodic_callback(self, *args: Any) -> None:
        """Repeatedly check the triggers to reset the timer."""
        await self.async_check_triggers()
        # Check if the segment has been disabled or we have transitioned
        # to a disabled segment.
        if not self.is_segment_enabled:
            await self.async_stop_dimmer()

    async def async_turn_on_dimmer(self, args: dict[str, Any]) -> None:
        """Turn the dimmer on."""
        args |= {
            ATTR_ENTITY_ID: self._data.dimmer,
        }
        await self.hass.services.async_call(
            LIGHT_DOMAIN,
            "turn_on",
            args,
        )

    async def async_turn_on_script(self) -> None:
        """Turn the script on."""
        if not self._data.script:
            return

        args = {
            ATTR_ENTITY_ID: self._data.script,
        }
        await self.hass.services.async_call(
            SCRIPT_DOMAIN,
            "turn_on",
            args,
        )

    def schedule_timer(
        self, next_time: datetime.datetime | None = None, duration: str | None = None
    ) -> None:
        """Start a timer."""

        if not next_time:
            seconds = self.seconds
            delay = datetime.timedelta(seconds=seconds)
            duration = str(delay)
            next_time = now() + delay
            self.cancel_timer()

        self._cancel_timer = async_track_point_in_time(
            self.hass,
            HassJob(
                self.async_schedule_callback,
                name="Dimmer Timer",
                cancel_on_shutdown=False,
            ),
            next_time,
        )

        self.track_timer(next_time, duration, SENSOR_ACTIVE)

    def init_timer(self) -> None:
        """Init timer."""

        if timer_end := self._attr_extra_state_attributes.get(SENSOR_END_TIME):
            duration = self._attr_extra_state_attributes.get(
                SENSOR_DURATION, "00:00:00"
            )
            next_time = datetime.datetime.fromisoformat(timer_end)
            self.schedule_timer(next_time, duration)

    def cancel_timer(self) -> None:
        """Stop the timer."""
        if self._cancel_timer is not None:
            self._cancel_timer()
            self._cancel_timer = None

        self.track_timer()

    def track_timer(
        self, timer_end=now(), duration="00:00:00", state=SENSOR_IDLE
    ) -> None:
        """Store changes in timer data so the timer sensor can read it."""
        new_attr = {
            SENSOR_END_TIME: timer_end,
            SENSOR_DURATION: duration,
        }
        self._attr_extra_state_attributes = new_attr
        timer_id = self.external_id(CE.TIMER)
        new_attr[ATTR_FRIENDLY_NAME] = self.hass.states.get(timer_id).attributes.get(
            ATTR_FRIENDLY_NAME
        )
        new_attr[ATTR_ICON] = self.hass.states.get(timer_id).attributes.get(ATTR_ICON)
        self.hass.states.async_set(
            entity_id=timer_id,
            new_state=state,
            attributes=new_attr,
        )

    def cancel_periodic_timer(self) -> None:
        """Cancel the periodic timer."""
        if self._cancel_periodic_timer is not None:
            self._cancel_periodic_timer()
            self._cancel_periodic_timer = None

    def schedule_periodic_timer(self) -> None:
        """Start the periodic timer to check triggers."""
        trigger_interval = self.trigger_interval
        if trigger_interval == 0:
            return

        delay = datetime.timedelta(seconds=trigger_interval)
        next_time = now() + delay
        self.cancel_periodic_timer()
        self._cancel_periodic_timer = async_track_point_in_time(
            self.hass,
            HassJob(
                self.async_periodic_callback,
                name="Dimmer Trigger Periodic Timer",
                cancel_on_shutdown=True,
            ),
            next_time,
        )

    def schedule_pump_timer(self) -> None:
        """Pump the dimmer for a short time."""
        delay = datetime.timedelta(seconds=1)
        next_time = now() + delay
        async_track_point_in_time(
            self.hass,
            HassJob(
                self.async_pump_callback,
                name="Dimmer Pump Timer",
                cancel_on_shutdown=True,
            ),
            next_time,
        )

    def add_time(self) -> None:
        """Add time to the timer."""
        if self._is_prediction:
            return

        self._additional_time = self.additional_time

    def reset_dimmer_time_on(self) -> None:
        """Reset dimmer time on."""
        if self._is_prediction:
            return
        self._dimmer_time_on = now()

    def reset_dimmer_time_off(self) -> None:
        """Reset dimmer time off."""
        if self._is_prediction:
            return
        self._dimmer_time_off = now()


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
    data.switch_object = switch
    async_add_entities([switch])

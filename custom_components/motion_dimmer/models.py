"""The motion_dimmer integration models."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_COLOR_MODE,
    ATTR_RGB_COLOR,
    ATTR_TRANSITION,
    ColorMode,
)
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.datetime import DOMAIN as DATETIME_DOMAIN
from homeassistant.components.script import DOMAIN as SCRIPT_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, ATTR_FRIENDLY_NAME, ATTR_ICON
from homeassistant.core import HassJob, HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import (
    async_track_point_in_time,
)
from homeassistant.util import slugify
from homeassistant.util.dt import now

from .const import (
    DOMAIN,
    LONG_TIME_OFF,
    PUMP_TIME,
    SENSOR_ACTIVE,
    SENSOR_DURATION,
    SENSOR_END_TIME,
    SENSOR_IDLE,
    SMALL_TIME_OFF,
    ControlEntityData,
)
from .const import (
    ControlEntities as CE,
)

_LOGGER = logging.getLogger(__name__)


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


def segments(hass: HomeAssistant, entry: ConfigEntry) -> dict:
    """Get the segments from the input select."""
    segs = {}
    data: MotionDimmerData = hass.data[DOMAIN][entry.entry_id]

    if data.input_select:
        input_segments = hass.states.get(data.input_select).attributes["options"]

        for input_segment in input_segments:
            segs[slugify(input_segment)] = input_segment

    return segs


@dataclass
class MotionDimmerData:
    """Data for the motion_dimmer integration."""

    device_id: str
    device_name: str
    dimmer: str
    input_select: str
    triggers: list
    predictors: list | None
    script: str | None
    motion_dimmer: MotionDimmer


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

        device_id = data.device_id
        self._device = device_id

        info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=data.device_name,
        )
        self._attr_device_info = info


class MotionDimmerAdapter:  # pragma: no cover
    """Adapter for Motion Dimmer"""

    @property
    def are_triggers_on(self) -> bool:
        """True if any triggers are on."""
        raise NotImplementedError

    @property
    def brightness_min(self) -> float:
        """The minimum brightness needed to activate the dimmer."""
        raise NotImplementedError

    @property
    def disabled_until(self) -> datetime:
        """The time Motion Dimmer is no longer disabled"""
        raise NotImplementedError

    @property
    def extension_max(self) -> float:
        """Maximum number of seconds the timer can be extended."""
        raise NotImplementedError

    @property
    def is_dimmer_on(self) -> bool:
        """Is the dimmer currently on."""
        raise NotImplementedError

    @property
    def is_segment_enabled(self) -> bool:
        """Return true if segment is enabled."""
        raise NotImplementedError

    @property
    def is_on(self) -> bool:
        """Is Motion Dimmer enabled"""
        raise NotImplementedError

    @property
    def manual_override(self) -> int:
        """The number of seconds to temprarily disable."""
        raise NotImplementedError

    @property
    def prediction_brightness(self) -> float:
        """The brightness of the predictive activation."""
        raise NotImplementedError

    @property
    def prediction_secs(self) -> float:
        """The number of seconds to activate a prediction."""
        raise NotImplementedError

    @property
    def brightness(self) -> float:
        """Get the brightness for the segment."""
        raise NotImplementedError

    @property
    def color_mode(self) -> str:
        """The color mode to set the dimmer to."""
        raise NotImplementedError

    @property
    def color_temp(self) -> int:
        """The color temp to set the dimmer to."""
        raise NotImplementedError

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        """The color to set the dimmer to."""
        raise NotImplementedError

    @property
    def seconds(self) -> float:
        """Get the number of seconds for the segment."""
        raise NotImplementedError

    @property
    def timer(self) -> TimerState:
        """Get the state of the timer."""
        raise NotImplementedError

    @property
    def trigger_interval(self) -> float:
        """Number of seconds to wait before checking the triggers again."""
        raise NotImplementedError

    def cancel_periodic_timer(self) -> None:
        """Cancel the periodic timer."""
        raise NotImplementedError

    def cancel_timer(self) -> None:
        """Stop the timer."""
        raise NotImplementedError

    def dimmer_state_callback(self, *args, **kwargs) -> dict:
        """Callback when dimmer state changes."""
        raise NotImplementedError

    def schedule_periodic_timer(self, time, callback) -> None:
        """Start the periodic timer to check triggers."""
        raise NotImplementedError

    def schedule_pump_timer(self, time, callback) -> None:
        """Pump the dimmer for a short time."""
        raise NotImplementedError

    def schedule_timer(self, time: datetime, duration: str, callback) -> None:
        """Start timer."""
        raise NotImplementedError

    def set_temporarily_disabled(self, next_time: datetime):
        """Set the temporarily disabled field"""
        raise NotImplementedError

    def track_timer(self, timer_end, duration, state) -> None:
        """Store changes in timer."""
        raise NotImplementedError

    def turn_on_dimmer(self, **kwargs) -> None:
        """Turn on dimmer."""
        raise NotImplementedError

    def turn_off_dimmer(self) -> None:
        """Turn off dimmer."""
        raise NotImplementedError

    def turn_on_script(self) -> None:
        """Turn on script."""
        raise NotImplementedError


class MotionDimmerHA(MotionDimmerAdapter):
    """Implementation of the adapter for Home Assistant"""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._hass = hass
        self._data: MotionDimmerData = hass.data[DOMAIN][entry_id]
        self._cancel_timer = None
        self._cancel_periodic_timer = None

    @property
    def are_triggers_on(self) -> bool:
        """True if any of the triggers are on."""
        for trigger in self.data.triggers:
            if self.hass.states.is_state(trigger, "on"):
                return True

        return False

    @property
    def brightness(self) -> int:
        """The brightness to set the dimmer to."""
        entity_id = self.external_id(CE.SEG_LIGHT, self.segment_id)
        if state := self.hass.states.get(entity_id):
            if bright := state.attributes.get(ATTR_BRIGHTNESS):
                return int(bright)

    @property
    def brightness_min(self) -> float:
        """The minimum brightness needed to activate the dimmer."""
        entity_id = self.external_id(CE.MIN_BRIGHTNESS)
        return float(self.hass.states.get(entity_id).state) * 2.55

    @property
    def color_mode(self) -> str:
        """The color mode to set the dimmer to."""
        return self.hass.states.get(
            self.external_id(CE.SEG_LIGHT, self.segment_id)
        ).attributes.get(ATTR_COLOR_MODE)

    @property
    def color_temp(self) -> int:
        """The color temp to set the dimmer to."""
        return self.hass.states.get(
            self.external_id(CE.SEG_LIGHT, self.segment_id)
        ).attributes.get(ATTR_COLOR_TEMP)

    @property
    def data(self) -> MotionDimmerData:
        """Return MotionDimmerData"""
        return self._data

    @property
    def disabled_until(self) -> datetime:
        """The datetime when the motion dimmer is no longer disabled."""
        state = self.hass.states.get(self.external_id(CE.DISABLED_UNTIL))
        if state:
            try:
                return datetime.fromisoformat(str(state.state))
            except ValueError:  # pragma: no cover
                return now()

    @property
    def extension_max(self) -> float:
        """Maximum number of seconds the timer can be extended."""
        entity_id = self.external_id(CE.EXTENSION_MAX)
        return float(self.hass.states.get(entity_id).state)

    @property
    def hass(self) -> HomeAssistant:
        """Return HomeAssistant"""
        return self._hass

    @property
    def is_dimmer_on(self) -> bool:
        """Is the dimmer currently on."""
        return self.hass.states.is_state(self.data.dimmer, "on")

    @property
    def is_segment_enabled(self) -> bool:
        """Return true if segment is enabled."""
        return self.hass.states.is_state(
            self.external_id(CE.SEG_LIGHT, self.segment_id), "on"
        )

    @property
    def is_on(self) -> bool:
        """Is Motion Dimmer enabled"""
        return self.hass.states.is_state(self.external_id(CE.CONTROL_SWITCH), "on")

    @property
    def manual_override(self) -> int:
        """The number of seconds to temprarily disable."""
        return int(self.hass.states.get(self.external_id(CE.MANUAL_OVERRIDE)).state)

    @property
    def prediction_brightness(self) -> float:
        """The brightness of the predictive activation."""
        entity_id = self.external_id(CE.PREDICTION_BRIGHTNESS)
        return float(self.hass.states.get(entity_id).state) * 255 / 100

    @property
    def prediction_secs(self) -> float:
        """The number of seconds to activate a prediction."""
        entity_id = self.external_id(CE.PREDICTION_SECS)
        return float(self.hass.states.get(entity_id).state)

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        """The color to set the dimmer to."""
        return self.hass.states.get(
            self.external_id(CE.SEG_LIGHT, self.segment_id)
        ).attributes.get(ATTR_RGB_COLOR)

    @property
    def seconds(self) -> float:
        """Number of seconds to turn the dimmer on."""
        entity_id = self.external_id(CE.SEG_SECONDS, self.segment_id)
        if state := self.hass.states.get(entity_id):
            return float(state.state)

    @property
    def segment_id(self) -> str:
        """The unique id of the segment."""
        segment = self.hass.states.get(self.data.input_select).state
        return slugify(segment)

    @property
    def timer(self) -> TimerState:
        """Get the state of the timer."""
        entity_id = self.external_id(CE.TIMER)
        timer = self.hass.states.get(entity_id)
        end_time = timer.attributes.get(SENSOR_END_TIME)
        end_time = datetime.fromisoformat(end_time) if end_time else now()
        duration = timer.attributes.get(SENSOR_DURATION) or "00:00:00"
        return TimerState(
            end_time,
            duration,
            timer.state,
        )

    @property
    def trigger_interval(self) -> float:
        """Number of seconds to wait before checking the triggers again."""
        entity_id = self.external_id(CE.TRIGGER_INTERVAL)
        return float(self.hass.states.get(entity_id).state)

    def cancel_timer(self) -> None:
        """Stop the timer."""
        if self._cancel_timer is not None:
            self._cancel_timer()
            self._cancel_timer = None

    def cancel_periodic_timer(self) -> None:
        """Cancel the periodic timer."""
        if self._cancel_periodic_timer is not None:
            self._cancel_periodic_timer()
            self._cancel_periodic_timer = None

    def dimmer_state_callback(
        self,
        changed_entity: str,
        old_state: State | None,
        new_state: State | None,
    ) -> DimmerStateChange:
        """Check if dimmer was changed manually."""
        return DimmerStateChange(
            old_state.state == "on" if old_state else False,
            new_state.state == "on" if new_state else False,
            old_state.attributes.get(ATTR_BRIGHTNESS) if old_state else None,
            new_state.attributes.get(ATTR_BRIGHTNESS) if new_state else None,
        )

    def external_id(
        self, ced: ControlEntityData, seg_id: str | None = None
    ) -> str | None:
        """Get the entity id from entity data."""
        return external_id(self.hass, ced, self.data.device_id, seg_id)

    def schedule_periodic_timer(self, time: datetime, callback) -> None:
        """Start the periodic timer to check triggers."""
        asyncio.run_coroutine_threadsafe(
            self.async_schedule_periodic_timer(time, callback), self.hass.loop
        ).result()

    async def async_schedule_periodic_timer(self, time: datetime, callback) -> None:
        """Start the periodic timer to check triggers."""
        self._cancel_periodic_timer = async_track_point_in_time(
            self.hass,
            HassJob(
                callback,
                name="Dimmer Trigger Periodic Timer",
                cancel_on_shutdown=True,
            ),
            time,
        )

    def schedule_pump_timer(self, time: datetime, callback) -> None:
        """Start the periodic timer to check triggers."""
        asyncio.run_coroutine_threadsafe(
            self.async_schedule_pump_timer(time, callback), self.hass.loop
        ).result()

    async def async_schedule_pump_timer(self, time: datetime, callback) -> None:
        """Pump the dimmer for a short time."""
        async_track_point_in_time(
            self.hass,
            HassJob(
                callback,
                name="Dimmer Pump Timer",
                cancel_on_shutdown=True,
            ),
            time,
        )

    def schedule_timer(self, time: datetime, duration: str, callback) -> None:
        """Start a timer."""
        asyncio.run_coroutine_threadsafe(
            self.async_schedule_timer(time, callback), self.hass.loop
        ).result()

    async def async_schedule_timer(self, time: datetime, callback) -> None:
        """Start a timer."""
        self._cancel_timer = async_track_point_in_time(
            self.hass,
            HassJob(
                callback,
                name="Dimmer Timer",
                cancel_on_shutdown=True,
            ),
            time,
        )

    def set_temporarily_disabled(self, next_time: datetime):
        """Set the temporarily disabled field"""
        asyncio.run_coroutine_threadsafe(
            self.async_set_temporarily_disabled(next_time), self.hass.loop
        ).result()

    async def async_set_temporarily_disabled(self, next_time: datetime) -> None:
        """Set the temporarily disabled field"""
        await self.hass.services.async_call(
            DATETIME_DOMAIN,
            "set_value",
            {
                "entity_id": self.external_id(CE.DISABLED_UNTIL),
                "datetime": next_time,
            },
        )

    def turn_on_dimmer(self, **kwargs) -> None:
        """Turn on dimmer."""
        asyncio.run_coroutine_threadsafe(
            self.async_turn_on_dimmer(**kwargs), self.hass.loop
        ).result()

    async def async_turn_on_dimmer(self, **kwargs) -> None:
        """Turn on dimmer."""
        args = {
            ATTR_ENTITY_ID: self.data.dimmer,
        }
        args[ATTR_BRIGHTNESS] = kwargs.get(ATTR_BRIGHTNESS)
        args[ATTR_TRANSITION] = kwargs.get(ATTR_TRANSITION)
        if kwargs.get(ATTR_COLOR_MODE) == ColorMode.COLOR_TEMP:
            args[ATTR_COLOR_TEMP] = kwargs.get(ATTR_COLOR_TEMP)
        if kwargs.get(ATTR_COLOR_MODE) == ColorMode.RGB:
            args[ATTR_RGB_COLOR] = kwargs.get(ATTR_RGB_COLOR)
        filtered_args = {k: v for k, v in args.items() if v is not None}
        await self.hass.services.async_call(
            LIGHT_DOMAIN,
            "turn_on",
            filtered_args,
        )

    def turn_off_dimmer(self) -> None:
        """Turn off dimmer."""
        asyncio.run_coroutine_threadsafe(
            self.async_turn_off_dimmer(), self.hass.loop
        ).result()

    async def async_turn_off_dimmer(self) -> None:
        """Turn off dimmer."""
        await self.hass.services.async_call(
            LIGHT_DOMAIN,
            "turn_off",
            {ATTR_ENTITY_ID: self.data.dimmer},
        )

    def turn_on_script(self) -> None:
        """Turn on script."""
        asyncio.run_coroutine_threadsafe(
            self.async_turn_on_script(), self.hass.loop
        ).result()

    async def async_turn_on_script(self) -> None:
        """Turn on script."""
        if not self.data.script:
            return

        args = {
            ATTR_ENTITY_ID: self.data.script,
        }
        await self.hass.services.async_call(
            SCRIPT_DOMAIN,
            "turn_on",
            args,
        )

    def track_timer(self, timer_end, duration, state) -> None:
        """Store changes in timer data so the timer sensor can read it."""
        asyncio.run_coroutine_threadsafe(
            self.async_track_timer(timer_end, duration, state), self.hass.loop
        ).result()

    async def async_track_timer(self, timer_end, duration, state) -> None:
        """Store changes in timer."""
        new_attr = {
            SENSOR_END_TIME: timer_end.isoformat(),
            SENSOR_DURATION: duration,
        }
        timer_id = self.external_id(CE.TIMER)
        new_attr[ATTR_FRIENDLY_NAME] = self.hass.states.get(timer_id).attributes.get(
            ATTR_FRIENDLY_NAME
        )
        new_attr[ATTR_ICON] = self.hass.states.get(timer_id).attributes.get(ATTR_ICON)
        self.hass.states.async_set(
            entity_id=timer_id, new_state=state, attributes=new_attr, force_update=True
        )


class MotionDimmer:
    """Representation of a Motion Dimmer."""

    def __init__(self, adapter: MotionDimmerAdapter) -> None:
        """Initialize the Motion Dimmer."""
        self._adapter = adapter
        self._is_prediction = False
        self._is_pumping = False
        self._was_dimmer_on = False
        self._additional_time = 0
        self._dimmer_time_on = now()
        self._dimmer_time_off = now()
        self._timer_end_time = now()
        self._timer_duration = "00:00:00"

    @property
    def adapter(self) -> MotionDimmerHA:
        """Get the storage adapter."""
        return self._adapter

    @property
    def dimmer_on_seconds(self) -> int:
        """Number of seconds the dimmer was on."""
        diff = now() - self._dimmer_time_on
        return round(diff.total_seconds())

    @property
    def dimmer_off_seconds(self) -> int:
        """Number of seconds the dimmer was off."""
        if self.adapter.is_dimmer_on:
            return 0

        diff = now() - self._dimmer_time_off
        return round(diff.total_seconds())

    @property
    def duration(self) -> str:
        """Get the duration."""
        return self._timer_duration

    @property
    def end_time(self) -> datetime:
        """Get the end time."""
        return self._timer_end_time

    @property
    def is_enabled(self) -> bool:
        """Return true if device is enabled."""
        # Motion Dimmer is on.
        if not self.adapter.is_on:
            return False

        # Motion Dimmer is not temporarily disabled.
        if self.is_temporarily_disabled:
            return False

        # Current segment is enabled.
        return self.adapter.is_segment_enabled

    @property
    def is_temporarily_disabled(self) -> bool:
        """Return true if device is temporarily disabled."""
        return now() < self.adapter.disabled_until

    @property
    def seconds(self) -> float:
        """Number of seconds to turn the dimmer on."""
        return self.adapter.seconds + self._additional_time

    def add_time(self) -> None:
        """Add time to the timer."""
        # Initialize the attribute.
        total = self._additional_time
        off_seconds = self.dimmer_off_seconds
        if off_seconds <= 0:
            # Light is on so only extend a small amount.
            total += int(self.dimmer_on_seconds / 5)
        elif off_seconds < SMALL_TIME_OFF:
            # Light was briefly off, so extend by normal amount
            total += self.dimmer_on_seconds
        elif off_seconds < LONG_TIME_OFF:
            # Light was off for a little while, so decrease the extension.
            total -= int(total / 2)
        else:
            # Light was off for long time.  Reset extension.
            total = 0

        # Make sure it is between 0 and max time.
        total = min(self.adapter.extension_max, max(total, 0))

        self._additional_time = total

    def dimmer_state_callback(self, *args, **kwargs) -> None:
        """Check if dimmer was changed manually."""
        if not self.is_enabled:
            return

        # Pass callback to adapter for platform-specific handling.
        change = self.adapter.dimmer_state_callback(*args, **kwargs)

        # Compare states.
        same_state = change.was_on == change.is_on
        same_bright = change.old_brightness == change.new_brightness
        # Don't worry about changes in color or temp.

        if not same_state:
            if change.is_on != self.adapter.are_triggers_on and not self._is_prediction:
                self.disable_temporarily()
        elif not same_bright and not self._is_pumping:
            # Give a 1 percent margin of error.
            diff = self.adapter.brightness - change.new_brightness
            if -1 < diff > 1:
                self.disable_temporarily()

    def disable_temporarily(self) -> None:
        """Disable all functionality for a time."""
        seconds = self.adapter.manual_override
        if seconds and int(seconds) > 0:
            delay = timedelta(seconds=int(seconds))
            next_time = now() + delay
        else:
            return  # pragma: no cover

        # Only set a new disable if it is later than the old one.
        if self.adapter.disabled_until < next_time:
            # Schedule the timer to turn off dimmer after it is reenabled.
            buffer = timedelta(seconds=5)
            self.adapter.schedule_timer(
                next_time + buffer, str(delay + buffer), self.timer_callback
            )
            self.adapter.set_temporarily_disabled(next_time)

    def init_timer(self, *args, **kwargs) -> None:
        """Init timer."""
        timer = self.adapter.timer
        self._timer_end_time = timer.end_time
        self._timer_duration = timer.duration

        # Check if timer was running on HA shutdown.
        if timer.end_time and timer.end_time > now():
            # Restart timer because it hasn't finished.
            self.schedule_timer(timer.end_time, timer.duration)
        elif timer.end_time and timer.state == SENSOR_ACTIVE:
            # Finish timer.
            self.timer_callback()

    def periodic_callback(self, *args, **kwargs) -> None:
        """Repeatedly check the triggers to reset the timer."""
        # Check if the segment has been disabled or we have transitioned
        # to a disabled segment.
        if self.is_enabled:
            if self.adapter.are_triggers_on:
                self.start_dimmer()
            else:
                self.schedule_periodic_timer()

    def predict(self):
        """Start the dimmer based on a prediction."""
        if self._is_prediction:
            # Prediction brightness is > minimum and < regular brightness.
            brightness = min(
                max(self.adapter.prediction_brightness, self.adapter.brightness_min),
                self.adapter.brightness,
            )
            delay = timedelta(seconds=self.adapter.prediction_secs)
            self.turn_on_dimmer(brightness)
            self.schedule_timer(now() + delay, str(delay))
            return True

        return False

    def predictor_callback(self, *args, **kwargs) -> None:
        """Run when predictors are activated."""
        # Do nothing if the dimmer is already on.
        if self.adapter.is_dimmer_on or not self.is_enabled:
            return

        self.start_dimmer(is_prediction=True)

    def pump(self) -> bool:
        """Start the dimmer at a brightness above the target brightness."""
        if (
            not self._was_dimmer_on
            and not self._is_pumping
            and not self._is_prediction
            and self.adapter.brightness < self.adapter.brightness_min
        ):
            self._is_pumping = True
            self.turn_on_dimmer(brightness=self.adapter.brightness_min)
            self.schedule_pump_timer()
            return True

        return False

    def pump_callback(self, *args, **kwargs) -> None:
        """Turn on the dimmer to normal brightness after pump."""
        if self.is_enabled:
            self.start_dimmer()

    def reset_dimmer_time_off(self) -> None:
        """Reset dimmer time off."""
        self._dimmer_time_off = now()

    def reset_dimmer_time_on(self) -> None:
        """Reset dimmer time on."""
        self._dimmer_time_on = now()

    def schedule_periodic_timer(self) -> None:
        """Start the periodic timer to check triggers."""
        trigger_interval = self.adapter.trigger_interval
        if trigger_interval == 0:
            return

        next_time = now() + timedelta(seconds=trigger_interval)
        self.adapter.cancel_periodic_timer()
        self.adapter.schedule_periodic_timer(next_time, self.periodic_callback)

    def schedule_pump_timer(self) -> None:
        """Pump the dimmer for a short time."""
        next_time = now() + timedelta(seconds=PUMP_TIME)
        self.adapter.schedule_pump_timer(next_time, self.pump_callback)

    def schedule_timer(
        self, next_time: datetime | None = None, duration: str | None = None
    ) -> None:
        """Start a timer."""

        if not next_time:
            seconds = self.seconds
            delay = timedelta(seconds=seconds)
            duration = str(delay)
            next_time = now() + delay

        self.adapter.cancel_timer()
        self.adapter.schedule_timer(next_time, duration, self.timer_callback)
        self.track_timer(next_time, duration, SENSOR_ACTIVE)

    def start_dimmer(self, is_prediction=False) -> None:
        """Turn on the dimmer."""
        # Predictions and Pumps are not considered "on".
        self._was_dimmer_on = (
            (not self._is_prediction)
            and (not self._is_pumping)
            and self.adapter.is_dimmer_on
        )
        # Prediction state must be set AFTER previous check.
        self._is_prediction = is_prediction

        if self.pump():
            return

        if self.predict():
            return

        self._is_pumping = False
        if not self._was_dimmer_on:
            self.reset_dimmer_time_on()

        self.add_time()
        self.turn_on_dimmer()
        self.schedule_timer()
        self.schedule_periodic_timer()

        # Only trigger the script if dimmer was off.
        if not self._was_dimmer_on:
            self.adapter.turn_on_script()

    def stop_dimmer(self) -> None:
        """Turn off the dimmer."""
        if self.adapter.is_on and not self.is_temporarily_disabled:
            # Check if triggers are are still on and make sure we turn off
            # the dimmer if the segment changed and the new one is disabled.
            if self.adapter.are_triggers_on and self.adapter.is_segment_enabled:
                # Restart everything instead of stopping.
                self.start_dimmer()
            else:
                self._is_prediction = False
                self.adapter.cancel_timer()
                self.adapter.cancel_periodic_timer()
                self.adapter.turn_off_dimmer()
                self.reset_dimmer_time_off()
                self.track_timer(now(), "00:00:00", SENSOR_IDLE)
        else:
            self.track_timer(now(), "00:00:00", SENSOR_IDLE)

    def timer_callback(self, *args, **kwargs) -> None:
        """Turn off the dimmer because timer ran out."""
        self.stop_dimmer()

    def track_timer(self, timer_end, duration, state) -> None:
        """Store changes in timer."""
        self._timer_end_time = timer_end
        self._timer_duration = duration
        self.adapter.track_timer(timer_end, duration, state)

    def triggered_callback(self, *args, **kwargs) -> None:
        """Run when triggers are activated."""
        if self.is_enabled:
            self.start_dimmer()

    def turn_on_dimmer(self, brightness: int | None = None):
        """Turn on the dimmer."""
        self.adapter.turn_on_dimmer(
            brightness=brightness or self.adapter.brightness,
            color_mode=self.adapter.color_mode,
            color_temp=self.adapter.color_temp,
            rgb_color=self.adapter.rgb_color,
            transition=1,
        )


@dataclass
class DimmerStateChange:
    """State change data."""

    was_on: bool
    is_on: bool
    old_brightness: int | None
    new_brightness: int | None


@dataclass
class TimerState:
    """Timer state data."""

    end_time: datetime
    duration: str
    state: str

"""Test Motion Dimmer setup process."""

import logging
from freezegun import freeze_time
from homeassistant.util.dt import utcnow
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import (
    async_capture_events,
)

from custom_components.motion_dimmer.const import (
    DEFAULT_SEG_SECONDS,
    DEFAULT_PREDICTION_SECS,
    DEFAULT_TRIGGER_INTERVAL,
    SMALL_TIME_OFF,
    LONG_TIME_OFF,
    ControlEntities,
)
from tests import (
    advance_time,
    dimmer_is_off,
    dimmer_is_set_to,
    get_timer_duration,
    let_dimmer_turn_off,
    set_number_field_to,
    set_segment_light_to,
    setup_integration,
    trigger_motion_dimmer,
    turn_off_trigger,
    turn_on_segment,
)


_LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR, force=True)


async def test_extension(hass: HomeAssistant):
    """Test the integration setup."""
    with freeze_time(utcnow()) as frozen_time:
        await setup_integration(hass)
        await turn_on_segment(hass)

        # Set the trigger interval to zero because we will be testing long durations.
        await set_number_field_to(hass, ControlEntities.TRIGGER_INTERVAL, 0)

        # Set the max extension to zero.
        await set_number_field_to(hass, ControlEntities.EXTENSION_MAX, 0)

        await trigger_motion_dimmer(hass)

        # Timer duration is the default.
        assert await get_timer_duration(hass) == DEFAULT_SEG_SECONDS

        old_duration = DEFAULT_SEG_SECONDS
        await advance_time(hass, DEFAULT_SEG_SECONDS - 5, frozen_time)
        await trigger_motion_dimmer(hass)

        # Timer did not extend.
        new_duration = await get_timer_duration(hass)
        assert new_duration == old_duration

        # Set the max extension to a higher number.
        max_extension = 200
        await set_number_field_to(hass, ControlEntities.EXTENSION_MAX, max_extension)

        # Timer duration increases on repeated triggers.
        old_duration = DEFAULT_SEG_SECONDS
        for i in range(3):
            await advance_time(hass, DEFAULT_SEG_SECONDS - 5, frozen_time)
            await trigger_motion_dimmer(hass)

            new_duration = await get_timer_duration(hass)
            assert new_duration > old_duration
            old_duration = new_duration

        assert new_duration > i * DEFAULT_SEG_SECONDS

        # Timer duration increases up to default plus max.
        for i in range(10):
            await advance_time(hass, DEFAULT_SEG_SECONDS - 5, frozen_time)
            await trigger_motion_dimmer(hass)

        new_duration = await get_timer_duration(hass)
        assert new_duration == max_extension + DEFAULT_SEG_SECONDS

        # Allow dimmer to turn off breifly.
        await turn_off_trigger(hass)
        events = async_capture_events(hass, "call_service")
        await advance_time(hass, new_duration + SMALL_TIME_OFF - 1, frozen_time)
        await dimmer_is_off(events)

        await trigger_motion_dimmer(hass)

        # Timer duration is still greater than the default.
        new_duration = await get_timer_duration(hass)
        assert new_duration > DEFAULT_SEG_SECONDS

        # Allow dimmer to turn off breifly.
        await turn_off_trigger(hass)
        events = async_capture_events(hass, "call_service")
        await advance_time(hass, new_duration + SMALL_TIME_OFF - 1, frozen_time)
        await dimmer_is_off(events)

        # Trigger a prediction.
        await trigger_motion_dimmer(hass, True)

        assert await get_timer_duration(hass) == DEFAULT_PREDICTION_SECS

        await trigger_motion_dimmer(hass)

        # Timer duration is still greater than the default.
        assert new_duration > DEFAULT_SEG_SECONDS

        # Allow dimmer to turn off for medium time.
        await turn_off_trigger(hass)
        events = async_capture_events(hass, "call_service")
        # Allow it to register as off.
        await advance_time(hass, new_duration, frozen_time)
        # Allow it to calculate time off.
        await advance_time(hass, LONG_TIME_OFF - 1, frozen_time)
        await dimmer_is_off(events)
        await trigger_motion_dimmer(hass)

        # Timer duration is reduced.
        new_duration = await get_timer_duration(hass)
        assert new_duration == DEFAULT_SEG_SECONDS + (max_extension / 2)

        # Allow dimmer to turn off for long time.
        await turn_off_trigger(hass)
        events = async_capture_events(hass, "call_service")
        # Allow it to register as off.
        await advance_time(hass, new_duration, frozen_time)
        # Allow it to calculate time off.
        await advance_time(hass, LONG_TIME_OFF, frozen_time)
        await dimmer_is_off(events)
        await trigger_motion_dimmer(hass)

        # Timer duration is back to default.
        new_duration = await get_timer_duration(hass)
        assert new_duration == DEFAULT_SEG_SECONDS

        await let_dimmer_turn_off(hass, frozen_time)


async def test_retrigger(hass: HomeAssistant):
    """Test the integration setup."""
    with freeze_time(utcnow()) as frozen_time:
        await setup_integration(hass)
        await turn_on_segment(hass)

        # Set the max extension to zero to keep test simple.
        await set_number_field_to(hass, ControlEntities.EXTENSION_MAX, 0)

        # Set the segment to be on for 10 minutes.
        ten_minutes = 60 * 10
        await set_number_field_to(hass, ControlEntities.SEG_SECONDS, ten_minutes)

        # Trigger dimmer and leave trigger on.
        await trigger_motion_dimmer(hass)

        # Retrigger happens until trigger is off.
        for i in range(5):
            events = async_capture_events(hass, "call_service")
            await advance_time(hass, DEFAULT_TRIGGER_INTERVAL, frozen_time)
            # Dimmer is turned on.
            await dimmer_is_set_to(events, {})

        # Turn off the segment.
        await set_segment_light_to(hass, "seg_1", "turn_off")
        events = async_capture_events(hass, "call_service")
        await advance_time(hass, DEFAULT_TRIGGER_INTERVAL, frozen_time)

        # Dimmer is turned off.
        await dimmer_is_off(events)

        # await let_dimmer_turn_off(hass, frozen_time)

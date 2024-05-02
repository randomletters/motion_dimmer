"""Test Motion Dimmer setup process."""

import logging
from freezegun import freeze_time
from homeassistant.util.dt import utcnow
from homeassistant.core import HomeAssistant, State
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
)
from pytest_homeassistant_custom_component.common import (
    async_capture_events,
    mock_state_change_event,
)

from custom_components.motion_dimmer.const import (
    DEFAULT_PREDICTION_BRIGHTNESS,
    DEFAULT_PREDICTION_SECS,
    DEFAULT_MANUAL_OVERRIDE,
    PUMP_TIME,
    ControlEntities,
)
from tests import (
    advance_time,
    dimmer_is_not_temporarily_disabled,
    dimmer_is_off,
    dimmer_is_set_to,
    from_pct,
    get_disable_delta,
    let_dimmer_turn_off,
    set_number_field_to,
    set_segment_light_to,
    setup_integration,
    event_extract,
    trigger_motion_dimmer,
    turn_off_trigger,
    turn_on_segment,
)

from .const import (
    MOCK_LIGHT_1_ID,
    SMALL_TIME,
)

logging.basicConfig(level=logging.ERROR, force=True)
_LOGGER = logging.getLogger(__name__)


async def test_pump(hass: HomeAssistant):
    """Test the minimum brightness."""
    with freeze_time(utcnow()) as frozen_time:
        config_entry = await setup_integration(hass)
        events = async_capture_events(hass, "call_service")

        await set_number_field_to(hass, ControlEntities.TRIGGER_INTERVAL, 0)
        await set_number_field_to(hass, ControlEntities.SEG_SECONDS, 10, "seg_1")
        await set_number_field_to(hass, ControlEntities.EXTENSION_MAX, 0)

        # Set current segment to brightness 3.
        await set_segment_light_to(hass, "seg_1", "turn_on", {ATTR_BRIGHTNESS: 3})

        events.clear()
        await trigger_motion_dimmer(hass, frozen_time)

        # Dimmer is set to brightness 3.
        await dimmer_is_set_to(events, {ATTR_BRIGHTNESS: 3})
        await dimmer_is_not_temporarily_disabled(hass)
        await let_dimmer_turn_off(hass, frozen_time)

        # Set minimum brightness 10.
        current_min_pct = 10
        await set_number_field_to(hass, ControlEntities.MIN_BRIGHTNESS, current_min_pct)

        await dimmer_is_not_temporarily_disabled(hass)

        events.clear()
        await trigger_motion_dimmer(hass, frozen_time)

        await dimmer_is_not_temporarily_disabled(hass)

        # Dimmer is set to brightness %10.
        await dimmer_is_set_to(events, {ATTR_BRIGHTNESS: from_pct(current_min_pct)})

        events.clear()

        # Let the pump subside.
        await advance_time(hass, PUMP_TIME, frozen_time)

        # Dimmer is set to brightness 3.
        await dimmer_is_set_to(events, {ATTR_BRIGHTNESS: 3})

        # Motion dimmer is not temporarily disabled.
        await dimmer_is_not_temporarily_disabled(hass)

        # Set current segment to brightness above current minimum.
        above = current_min_pct + 10
        await set_segment_light_to(
            hass, "seg_1", "turn_on", {ATTR_BRIGHTNESS: from_pct(above)}
        )

        events.clear()
        await trigger_motion_dimmer(hass, frozen_time)

        # Dimmer is set to brightness above current minimum.
        await dimmer_is_set_to(events, {ATTR_BRIGHTNESS: from_pct(above)})
        await dimmer_is_not_temporarily_disabled(hass)

        events.clear()
        # # Finish timers.
        await let_dimmer_turn_off(hass, frozen_time)
        await dimmer_is_not_temporarily_disabled(hass)

        assert await config_entry.async_unload(hass)
        await hass.async_block_till_done()

        # assert events == []

        # async def test_prediction(hass: HomeAssistant):
        #     """Test the integration setup."""
        #     with freeze_time(utcnow()) as frozen_time:
        #         config_entry = await setup_integration(hass)
        #         await turn_on_segment(hass)

        #         # Trigger a prediction.
        #         events = await trigger_motion_dimmer(hass, True)

        #         # Dimmer is set to prediction brightness.
        #         await dimmer_is_set_to(
        #             events, {ATTR_BRIGHTNESS: from_pct(DEFAULT_PREDICTION_BRIGHTNESS)}
        #         )
        #         await dimmer_is_not_temporarily_disabled(hass)

        #         # Allow prediction to finish.
        #         events = async_capture_events(hass, "call_service")
        #         await advance_time(hass, DEFAULT_PREDICTION_SECS, frozen_time)

        #         await dimmer_is_off(events)
        #         await dimmer_is_not_temporarily_disabled(hass)

        # # Trigger the dimmer normally.
        # events = await trigger_motion_dimmer(hass)

        # # Dimmer is set to brightness 255.
        # await dimmer_is_set_to(events, {ATTR_BRIGHTNESS: 255})
        # await dimmer_is_not_temporarily_disabled(hass)

        # # Trigger a prediction while dimmer is still on.
        # events = await trigger_motion_dimmer(hass, True)

        # # Dimmer is not changed.
        # assert event_extract(events, "domain") is None
        # await dimmer_is_not_temporarily_disabled(hass)

        # await let_dimmer_turn_off(hass, frozen_time)

        # # Trigger a prediction.
        # events = await trigger_motion_dimmer(hass, True)

        # # Dimmer is set to prediction brightness.
        # await dimmer_is_set_to(
        #     events, {ATTR_BRIGHTNESS: from_pct(DEFAULT_PREDICTION_BRIGHTNESS)}
        # )
        # await dimmer_is_not_temporarily_disabled(hass)

        # # Don't allow prediction to finish.
        # events = await trigger_motion_dimmer(hass)

        # # Dimmer is now set to brightness 255.
        # await dimmer_is_set_to(events, {ATTR_BRIGHTNESS: 255})
        # await dimmer_is_not_temporarily_disabled(hass)

        # await let_dimmer_turn_off(hass, frozen_time)

        # assert await config_entry.async_unload(hass)
        # await hass.async_block_till_done()

        # async def test_temp_disable(hass: HomeAssistant):
        #     """Test the integration setup."""
        #     with freeze_time(utcnow()) as frozen_time:
        #         config_entry = await setup_integration(hass)
        #         await turn_on_segment(hass)

        #         # Turn on light manually.
        #         mock_state_change_event(
        #             hass, State(MOCK_LIGHT_1_ID, "on"), State(MOCK_LIGHT_1_ID, "off")
        #         )
        #         await hass.async_block_till_done()

        #         # Let time pass to prevent event overlap.
        #         await advance_time(hass, SMALL_TIME, frozen_time)

        #         # Motion dimmer is temporarily disabled.
        #         assert get_disable_delta(hass) > 1

        #         # Try to trigger while temp disabled.
        #         events = await trigger_motion_dimmer(hass)

        #         # Dimmer is still off.
        #         assert event_extract(events, "domain") is None
        #         await turn_off_trigger(hass)

        #         events = async_capture_events(hass, "call_service")

        #         # Let manual override (plus the buffer) time pass.
        #         await advance_time(hass, DEFAULT_MANUAL_OVERRIDE + 5, frozen_time)

        #         await dimmer_is_off(events)
        #         await dimmer_is_not_temporarily_disabled(hass)

        # # Turn on dimmer.
        # events = await trigger_motion_dimmer(hass)
        # await dimmer_is_not_temporarily_disabled(hass)

        # # Turn off dimmer manually.
        # mock_state_change_event(
        #     hass, State(MOCK_LIGHT_1_ID, "off"), State(MOCK_LIGHT_1_ID, "on")
        # )
        # await hass.async_block_till_done()

        # # Allow time for events to resolve.
        # await advance_time(hass, 5, frozen_time)

        # # Motion dimmer is temporarily disabled.
        # assert get_disable_delta(hass) > 1

        # # Wait until enabled again.
        # await advance_time(hass, get_disable_delta(hass) + 100, frozen_time)

        # # Turn on dimmer.
        # events = await trigger_motion_dimmer(hass)
        # await dimmer_is_not_temporarily_disabled(hass)

        # # Change dimmer brightness.
        # mock_state_change_event(
        #     hass,
        #     State(MOCK_LIGHT_1_ID, "on", {ATTR_BRIGHTNESS: 50}),
        #     State(MOCK_LIGHT_1_ID, "on"),
        # )
        # await hass.async_block_till_done()

        # # Allow time for events to resolve.
        # await advance_time(hass, 5, frozen_time)

        # # Motion dimmer is temporarily disabled.
        # assert get_disable_delta(hass) > 1

        # await let_dimmer_turn_off(hass, frozen_time)

        # assert await config_entry.async_unload(hass)
        # await hass.async_block_till_done()

"""Test Motion Dimmer setup process."""

import logging
from copy import deepcopy
from datetime import datetime, timedelta
from homeassistant.util.dt import utcnow, now
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_RGB_COLOR,
    ATTR_TRANSITION,
)

from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.motion_dimmer.const import (
    DOMAIN,
    ControlEntities,
    SERVICE_DISABLE,
    SERVICE_ENABLE,
    SERVICE_FINISH_TIMER,
    SERVICE_HOURS,
    SERVICE_MINUTES,
    SERVICE_SECONDS,
    SENSOR_DURATION,
    SENSOR_END_TIME,
)
from custom_components.motion_dimmer.models import external_id, segments

from .const import (
    CONFIG_NAME,
    MOCK_CONFIG,
    MOCK_INPUT_SELECT,
    MOCK_OPTIONS,
    MOCK_LIGHTS,
    MOCK_BINARY_SENSORS,
    INPUT_SELECT_DOMAIN,
    BINARY_SENSOR_DOMAIN,
    LIGHT_DOMAIN,
)

CONF_ID = "12345"

_LOGGER = logging.getLogger(__name__)


async def setup_integration(
    hass: HomeAssistant,
    *,
    config=MOCK_CONFIG,
    options=MOCK_OPTIONS,
    entry_id="1",
    unique_id=CONF_ID,
    source=SOURCE_USER,
):
    """Create the integration."""

    await async_setup_component(hass, INPUT_SELECT_DOMAIN, MOCK_INPUT_SELECT)
    await hass.async_block_till_done()
    await async_setup_component(hass, LIGHT_DOMAIN, MOCK_LIGHTS)
    await hass.async_block_till_done()
    await async_setup_component(hass, BINARY_SENSOR_DOMAIN, MOCK_BINARY_SENSORS)
    await hass.async_block_till_done()

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=source,
        data=deepcopy(config),
        options=deepcopy(options),
        entry_id=entry_id,
        unique_id=unique_id,
    )
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    return config_entry


async def test_setup(hass: HomeAssistant):
    """Test the integration setup."""
    config_entry = await setup_integration(hass)
    assert segments(hass, config_entry) == {"seg_1": "Seg 1", "seg_2": "Seg 2"}
    entity_id = external_id(hass, ControlEntities.CONTROL_SWITCH, CONFIG_NAME)
    assert hass.states.get(entity_id).state == "on"
    entity_id = external_id(hass, ControlEntities.EXTENSION_MAX, CONFIG_NAME)
    assert hass.states.get(entity_id).state == "3600"
    entity_id = external_id(hass, ControlEntities.MANUAL_OVERRIDE, CONFIG_NAME)
    assert hass.states.get(entity_id).state == "600"
    entity_id = external_id(hass, ControlEntities.MIN_BRIGHTNESS, CONFIG_NAME)
    assert hass.states.get(entity_id).state == "1"
    entity_id = external_id(hass, ControlEntities.PREDICTION_BRIGHTNESS, CONFIG_NAME)
    assert hass.states.get(entity_id).state == "50"
    entity_id = external_id(hass, ControlEntities.PREDICTION_SECS, CONFIG_NAME)
    assert hass.states.get(entity_id).state == "10"
    entity_id = external_id(hass, ControlEntities.SEG_LIGHT, CONFIG_NAME, "seg_1")
    assert hass.states.get(entity_id).state == "off"
    entity_id = external_id(hass, ControlEntities.SEG_SECONDS, CONFIG_NAME, "seg_1")
    assert hass.states.get(entity_id).state == "60"
    entity_id = external_id(hass, ControlEntities.SEG_LIGHT, CONFIG_NAME, "seg_2")
    assert hass.states.get(entity_id).state == "off"
    entity_id = external_id(hass, ControlEntities.SEG_SECONDS, CONFIG_NAME, "seg_2")
    assert hass.states.get(entity_id).state == "60"
    entity_id = external_id(hass, ControlEntities.TRIGGER_INTERVAL, CONFIG_NAME)
    assert hass.states.get(entity_id).state == "60"

    assert hass.states.get("light.test_light_1").state == "off"
    assert hass.states.get("binary_sensor.test_binary_sensor_1").state == "off"
    assert hass.states.get("switch.test_config_motion_dimmer").state == "on"


async def test_timers(hass: HomeAssistant):
    """Test the integration setup."""
    config_entry = await setup_integration(hass)
    # entity_id = external_id(hass, ControlEntities.MIN_BRIGHTNESS, CONFIG_NAME)

    hass.states.async_set(
        "light.test_config_option_seg_1", "on", attributes={ATTR_BRIGHTNESS: 50}
    )
    await hass.async_block_till_done()
    hass.states.async_set("binary_sensor.test_binary_sensor_1", "on")
    await hass.async_block_till_done()
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    assert hass.states.get("light.test_light_1").state == "on"
    # _LOGGER.warning(f"{hass.states.get("light.test_light_1").attributes}")
    # assert hass.states.get("light.test_light_1").attributes.get(ATTR_BRIGHTNESS) == 50
    hass.states.async_set("binary_sensor.test_binary_sensor_1", "off")
    await hass.async_block_till_done()
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=60))
    assert hass.states.get("light.test_light_1").state == "off"


async def test_services(hass: HomeAssistant):
    """Test the integration setup."""
    config_entry = await setup_integration(hass)

    disable_id = external_id(hass, ControlEntities.DISABLED_UNTIL, CONFIG_NAME)
    setting = datetime.fromisoformat(hass.states.get(disable_id).state)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_DISABLE,
        {
            "entity_id": disable_id,
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    delay_id = external_id(hass, ControlEntities.MANUAL_OVERRIDE, CONFIG_NAME)
    delay = timedelta(seconds=int(hass.states.get(delay_id).state))
    # assert (setting + delay).isoformat() == hass.states.get(disable_id).state

    delta = now() - datetime.fromisoformat(hass.states.get(disable_id).state)
    # assert delta.seconds > 1
    await hass.services.async_call(
        DOMAIN,
        SERVICE_ENABLE,
        {
            "entity_id": disable_id,
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    delta = now() - datetime.fromisoformat(hass.states.get(disable_id).state)
    # assert delta.seconds < 1

    switch_id = external_id(hass, ControlEntities.CONTROL_SWITCH, CONFIG_NAME)
    # attr = hass.states.get(switch_id).attributes
    # assert attr.get(SENSOR_END_TIME) is None
    # assert attr.get(SENSOR_DURATION) is None

    hass.states.async_set(
        "light.test_config_option_seg_1", "on", attributes={ATTR_BRIGHTNESS: 50}
    )

    hass.states.async_set("binary_sensor.test_binary_sensor_1", "on", force_update=True)
    # hass.bus.async_fire(BINARY_SENSOR_EVENT_TYPE, event_data=BINARY_SENSOR_EVENT_DATA)
    await hass.async_block_till_done()
    attr = hass.states.get(switch_id).attributes
    delta = now() - datetime.fromisoformat(attr.get(SENSOR_END_TIME))
    assert delta.seconds > 1
    assert attr.get(SENSOR_DURATION) != "00:00:00"

    timer_id = external_id(hass, ControlEntities.TIMER, CONFIG_NAME)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_FINISH_TIMER,
        {
            "entity_id": timer_id,
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    attr = hass.states.get(switch_id).attributes
    delta = now() - datetime.fromisoformat(attr.get(SENSOR_END_TIME))
    assert delta.seconds < 1
    assert attr.get(SENSOR_DURATION) == "00:00:00"
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=60))

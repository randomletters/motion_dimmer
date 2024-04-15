"""Constants for Motion Dimmer tests."""

from homeassistant.components.input_select import DOMAIN as INPUT_SELECT_DOMAIN

from custom_components.motion_dimmer.const import (
    CONF_DIMMER,
    CONF_FRIENDLY_NAME,
    CONF_INPUT_SELECT,
    CONF_PREDICTERS,
    CONF_SCRIPT,
    CONF_TRIGGERS,
    CONF_UNIQUE_NAME,
)

CONFIG_NAME = "test_id"
MOCK_CONFIG = {
    CONF_UNIQUE_NAME: CONFIG_NAME,
    CONF_FRIENDLY_NAME: "Test Config",
}

MOCK_OPTIONS = {
    CONF_DIMMER: "light.kitchen_island",
    CONF_INPUT_SELECT: "input_select.test_input_select",
    CONF_TRIGGERS: ["binary_sensor.kitchen_island_motion"],
    CONF_PREDICTERS: ["binary_sensor.kitchen_nook_motion"],
    CONF_SCRIPT: "script.kitchen_island_script",
}

MOCK_INPUT_SELECT = {
    INPUT_SELECT_DOMAIN: {
        "test_input_select": {
            "options": ["Seg 1", "Seg 2"],
            "name": "Test Input Select",
            "initial": "Seg 1",
            # "unique_id": "test_input_select",
        }
    }
}

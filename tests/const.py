"""Constants for Motion Dimmer tests."""

from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.input_select import DOMAIN as INPUT_SELECT_DOMAIN
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN

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
    CONF_DIMMER: "light.test_light_1",
    CONF_INPUT_SELECT: "input_select.test_input_select",
    CONF_TRIGGERS: ["binary_sensor.test_binary_sensor_1"],
    CONF_PREDICTERS: ["binary_sensor.kitchen_nook_motion"],
    CONF_SCRIPT: "",  # "script.kitchen_island_script",
}

MOCK_INPUT_SELECT = {
    INPUT_SELECT_DOMAIN: {
        "test_input_select": {
            "options": ["Seg 1", "Seg 2"],
            "name": "Test Input Select",
            "initial": "Seg 1",
        }
    }
}

MOCK_BINARY_SENSORS = {
    BINARY_SENSOR_DOMAIN: [
        {
            "platform": "template",
            "sensors": {
                "test_binary_sensor_1": {
                    "friendly_name": "Test Binary Sensor 1",
                    "value_template": "{{false}}",
                }
            },
        }
    ]
}

MOCK_LIGHTS = {
    LIGHT_DOMAIN: [
        {
            "platform": "template",
            "lights": {
                "test_light_1": {
                    "friendly_name": "Test Light 1",
                    "supports_transition_template": True,
                    "set_temperature": None,
                    "set_rgb": None,
                    "turn_on": None,
                    "turn_off": None,
                    "set_level": None,
                },
                "test_light_2": {
                    "friendly_name": "Test Light 2",
                    "turn_on": None,
                    "turn_off": None,
                    "set_level": None,
                },
            },
        }
    ]
}

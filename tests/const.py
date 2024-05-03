"""Constants for Motion Dimmer tests."""

from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.input_select import DOMAIN as INPUT_SELECT_DOMAIN
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.number import DOMAIN as NUMBER_DOMAIN
from homeassistant.components.script import DOMAIN as SCRIPT_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN

from custom_components.motion_dimmer.const import (
    CONF_DIMMER,
    CONF_FRIENDLY_NAME,
    CONF_INPUT_SELECT,
    CONF_PREDICTORS,
    CONF_SCRIPT,
    CONF_TRIGGERS,
    CONF_UNIQUE_NAME,
)

SMALL_TIME = 2

CONFIG_NAME = "test_id"
MOCK_CONFIG = {
    CONF_UNIQUE_NAME: CONFIG_NAME,
    CONF_FRIENDLY_NAME: "Test Config",
}

MOCK_LIGHT_1 = "test_light_1"
MOCK_LIGHT_1_ID = LIGHT_DOMAIN + "." + MOCK_LIGHT_1
MOCK_LIGHT_2 = "test_light_2"
MOCK_LIGHT_2_ID = LIGHT_DOMAIN + "." + MOCK_LIGHT_2
MOCK_BINARY_SENSOR_1 = "test_binary_sensor_1"
MOCK_BINARY_SENSOR_1_ID = BINARY_SENSOR_DOMAIN + "." + MOCK_BINARY_SENSOR_1
MOCK_BINARY_SENSOR_2 = "test_binary_sensor_2"
MOCK_BINARY_SENSOR_2_ID = BINARY_SENSOR_DOMAIN + "." + MOCK_BINARY_SENSOR_2
MOCK_SCRIPT = "test_script"
MOCK_SCRIPT_ID = SCRIPT_DOMAIN + "." + MOCK_SCRIPT


MOCK_OPTIONS = {
    CONF_DIMMER: MOCK_LIGHT_1_ID,
    CONF_INPUT_SELECT: "input_select.test_input_select",
    CONF_TRIGGERS: [MOCK_BINARY_SENSOR_1_ID],
    CONF_PREDICTORS: [MOCK_BINARY_SENSOR_2_ID],
    CONF_SCRIPT: MOCK_SCRIPT_ID,
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
                MOCK_BINARY_SENSOR_1: {
                    "friendly_name": "Test Binary Sensor 1",
                    "value_template": "{{false}}",
                },
                MOCK_BINARY_SENSOR_2: {
                    "friendly_name": "Test Binary Sensor 2",
                    "value_template": "{{false}}",
                },
            },
        }
    ]
}


MOCK_LIGHTS = {
    LIGHT_DOMAIN: [
        {
            "platform": "template",
            "lights": {
                MOCK_LIGHT_1: {
                    "friendly_name": "Test Light 1",
                    "supports_transition_template": True,
                    "set_temperature": None,
                    "set_rgb": None,
                    "turn_on": None,
                    "turn_off": None,
                    "set_level": None,
                },
                MOCK_LIGHT_2: {
                    "friendly_name": "Test Light 2",
                    "turn_on": None,
                    "turn_off": None,
                    "set_level": None,
                },
            },
        }
    ]
}

MOCK_SCRIPTS = {
    SCRIPT_DOMAIN: {
        MOCK_SCRIPT: {
            "sequence": {
                "service": "light.turn_on",
                "data": {"entity_id": MOCK_LIGHT_2_ID},
            }
        }
    }
}

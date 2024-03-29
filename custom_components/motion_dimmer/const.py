"""Constants for the Motion Dimmers integration."""

from dataclasses import dataclass
from enum import Enum

from homeassistant.const import Platform

DOMAIN = "motion_dimmer"

CONF_UNIQUE_NAME = "unique_name"
CONF_FRIENDLY_NAME = "friendly_name"
CONF_DIMMER = "dimmer"
CONF_INPUT_SELECT = "input_select"
CONF_TRIGGERS = "triggers"
CONF_PREDICTERS = "predicters"

# Control Entities

PLATFORM = "platform"


@dataclass
class ControlEntityData:
    """Data for the motion_dimmer integration."""

    platform: str
    id_suffix: str


class ControlEntities(ControlEntityData, Enum):
    """Entities used to control functionality."""

    DISABLED_UNTIL = (Platform.DATETIME, "disabled_until")
    MIN_BRIGHTNESS = (Platform.NUMBER, "brightness_min")
    TRIGGER_INTERVAL = (Platform.NUMBER, "trigger_interval")
    EXTENSION_MAX = (Platform.NUMBER, "extension_max")
    MANUAL_OVERRIDE = (Platform.NUMBER, "manual_override")
    PREDICTION_SECS = (Platform.NUMBER, "prediction_secs")
    PREDICTION_BRIGHTNESS = (Platform.NUMBER, "prediction_brightness")
    SEG_SECONDS = (Platform.NUMBER, "seconds")
    SEG_LIGHT = (Platform.LIGHT, "light")
    CONTROL_SWITCH = (Platform.SWITCH, "control")
    TIMER = (Platform.SENSOR, "timer")
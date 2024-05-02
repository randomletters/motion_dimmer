# Motion Dimmer

Have a dimmer respond differently to a motion trigger depending on several criteria.

## Dropdown Helper

A Motion Dimmer must be associated with a dropdown helper (input_select). Each option in the dropdown will create entities to set the light parameters (brightness, color temp, rgb) as well as a duration for that dropdown option. [More...](#dropdown-options)

### Note

You will need to restart Home Assistant if you change any options in the dropdown.

## Setup

When adding a Motion Dimmer you must first enter:

- `Name`: The name of the Motion Dimmer, for example "Kitchen Island"
- `Unique Id`: The unique id, for example: “kitchen_island”

Once added, click on "Configure" and fill out the following fields (\* required):

- `Dimmer*`: This is the light entity that will be controlled.
- `Dropdown Helper*`: The dropdown that will define and control which settings are active.
- `Triggers*`: The main binary sensors that will fully activate the dimmer.
- `Predictors`: Any adjacent binary sensors that will briefly activate the dimmer.
- `Script`: A script that will run after the dimmer is triggered. [More...](#scripts)

Once configured, you can edit the entities that control the Motion Dimmer by going to the device.

- `Option: [dropdown_option]`: This light entity stores the state to display when triggered. There will be one light entity per dropdown_option. Turning this control off disables the dimmer until the dropdown helper changes to another option. If you are controlling a smart light with color functionality and do not want the Motion Dimmer to update the color, set the brightness and press the “White” mode button so no color information is sent when activated.
- `Option: [dropdown option]`: This number entity determines the number of seconds the light will be activated. [More...](#timers)
- `Motion Dimmer`: This switch enables and disables all Motion Dimmer functionality. When off, the dimmer will function as a normal dimmer, with no motion functionality.
- `Manual Override Time`: The number of seconds to disable the Motion Dimmer when the dimmer is manually operated. Set this to 0 if you do not want the Motion Dimmer to be disabled automatically. [More...](#manual-override-time)
- `Disabled Until`: When a Motion Dimmer is manually overridden, the “Disabled Until” datetime is set to the future. The Motion Dimmer will not activate until after that time. You can manually set this time if you want the dimmer to be deactivated temporarily.
- `Trigger Test Interval`: This is the number of seconds before the trigger is polled to see if it is still on. If the trigger is still on, Motion Dimmer will restart the timer with an extended time. Set this number to 0 if you don’t want the Motion Dimmer to restart the timer. Each time the trigger turns on, the Motion Dimmer will restart the timer even without a test interval. [More...](#trigger-test-interval)
- `Max Extension`: This is the maximum number of seconds that the Motion Dimmer can add to the original timer. Set this number to 0 if you want the dimmer to only be on for the specified amount of time. [More...](#max-extension)
- `Prediction Time`: When a predictor in an adjacent room is activated the light is turned on for the amount of time set here. [More...](#prediction-time)
- `Prediction Brightness`: Set this to the brightness you want when you are not sure you will be entering the adjacent room. [More...](#prediction-brightness)
- `Minimum brightness`: If the Motion Dimmer brightness is set to a number lower than the minimum brightness, the light will first turn on at the minimum brightness for 1 second and then immediately lower to the correct brightness. [More...](#minimum-brightness)

### Note

All of these entities can be manipulated with automations and scenes to add more sophisticated functionality. Adding these entities to groups can allow for convenient dashboards as well.

## Services

Motion Dimmer provides 3 services:

- `temporarily_disable`: Disables the Motion Dimmer for a short time. Uses the default time if **_hours_**, **_minutes_**, or **_seconds_** are not specified. This is much easier than home assistant date math templates.
- `enable`: Reenables a Motion Dimmer by resetting the Disabled Until field.
- `finish_timer`: Ends the timer early, causing the dimmer to turn off if the trigger is not active. The timer will restart if the trigger is still active.

## Timer

Motion Dimmer also provides a sensor which tracks the timer. The state and attributes can be used in conjunction with the [Timer Bar Card](https://github.com/rianadon/timer-bar-card) custom integration to display a countdown timer in dashboards.

## More Details

### Dropdown Options

Here is an example of how you might set up the dropdown options:

| Option       | Dimmer Setting                                |
| ------------ | --------------------------------------------- |
| **Day**      | Cool color temp, 100% brightness, 30 seconds. |
| **Night**    | Warm color temp, 50% brightness, 10 minutes.  |
| **Sleeping** | "Red", 1% brightness, 10 seconds.             |

When you change the option manually or via an automation, the Motion Dimmer will automatically use the new settings.

### Scripts

Scripts are only activated when the dimmer is first triggered from "off" (or mid prediction mode). Often you might want to have something happen when the lights turn on, but not every time motion is sensed. If you use Motion Dimmer predicters, then you can't trigger based on the dimmer state. Instead you can create a script and Motion Dimmer will only call it on actual triggers, not prediction triggers. It will not be called again until the dimmer is off.

### Timers

When a Motion Dimmer is triggered, an internal timer is started. This timer will persist across Home Assistant restarts.

### Manual Override Time

Turning the light on when not triggered, off when triggered, or changing the brightness to something other than the programmed brightness will cause the Motion Dimmer to be disabled for the amount of time specified. Changes in color do not disable the motion dimmer. This allows the dimmer to work in conjunction with integrations like [Adaptive Lighting](https://github.com/basnijholt/adaptive-lighting) that adjust the color temperature of the light over time.

### Trigger Test Interval

Different motion sensors have different timeouts for sensing. This field should be set to a number greater than the motion sensor timeout so it can determine if the motion sensor is still detecting motion. Instead of starting the timer when the sensor turns off, it is polled periodically after it starts, which allows for more sophisticated behavior. The timer can be extended if the room is continually occupied. Also, if the dropdown helper is changed to a new setting, the dimmer will change to the correct value at the end of the test interval. This functionality allows you to set the initial time to a smaller number and trust that the Motion Dimmer will keep the light on until there is no motion, which is very helpful in rooms like tv rooms where you spend a lot of time with little motion.

### Max Extension

Set this to a low number (maybe 60 seconds) in rooms that have high traffic and low continuous activity like hallways. Set this number higher (maybe 3600 seconds) in rooms that have long activity times but intervals of little motion like TV rooms. If a dimmer goes off for a short period of time (less than 20 seconds) and is immediately retriggered, the extension will persist. If the dimmer is off for a medium amount of time (less than 20 minutes), the extension will be halved. If it is off for longer, the extension is reset. This dramatically reduces the amount of times people have to "flail their arms around" when motion sensors fail to sense them.

### Prediction Time

Often when you enter a room with a motion sensor the light doesn’t turn on until you are well within the room. If you have motion sensors in adjacent rooms you can set them as predictors. If configured correctly, you will never have to enter a dark room again.

### Prediction Brightness

You might set this to a low brightness that just barely illuminates the room. Then, if you activate the main trigger, the Motion Dimmer will turn on the dimmer to full configured settings. Prediction Brightness will not cause the dimmer to go brighter than the current dropdown option brightness even if it is set higher. If you don't enter the room and activate the main trigger, the dimmer will turn back off after the time specified in Prediction Time.

### Minimum Brightness

Some bulbs won’t turn on if you go from **_off_** to **_1%_**, but they will work if you start from a higher brightness. Minimum brightness is the percent that the light needs to activate before being lowered to the desired brightness. This is great for scenarios like getting up in the middle of the night where your eyes are very sensitive to light.

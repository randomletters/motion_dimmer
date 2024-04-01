# Motion Dimmer 
Have a dimmer respond differently to a motion trigger depending on several criteria.

## Dropdown Helper
A Motion Dimmer must be associated with a dropdown helper (input_select).  Each option in the dropdown will create entities to set the light parameters (brightness, color temp, rgb) as well as a duration for that dropdown option.
For example:  if you create a dropdown for segments of the day like: Day, Night, and Sleeping…
You could set a cool color temp at full brightness during the day, warm color temp at night with 50% brightness, and red light at 1% at night.

When adding a Motion Dimmer you must first enter:

- `Name:` The name of the Motion Dimmer, for example "Kitchen Island"
- `Unique Id:` The unique id, for example: “kitchen_island”

Once added, click on "Configure" and fill out the following fields (* required):

- `Dimmer*:` This is the light entity that will be controlled.
- `Dropdown Helper*:`  The dropdown that will define and control which settings are active.
- `Triggers*:`  The main binary sensors that will fully activate the dimmer.
- `Predictors:`  Any adjacent binary sensors that will briefly activate the dimmer.

Once configured, you can edit the entities that control the Motion Dimmer by going to the device.

- `[Dropdown Item] Light Settings:`  This is a light entity that stores the state to display when activated.  There will be one light entity per dropdown option.  Turning the control off disables the dimmer until the dropdown helper changes to another option.  If you are controlling a smart light with color functionality, but do not want the Motion Dimmer to update the color, set the brightness and press the “White” light button so no color information is sent when activated.
- `[Dropdown Item] Seconds:`  This determines the number of seconds the light will be activated.
- `Motion Dimmer switch:`  This enables and disables the Motion Dimmer functionality.  When off, the dimmer will function as a normal dimmer, with no motion functionality.
- `Manual Override Time:`  Turning the light on when not triggered, off when triggered, or changing the brightness to something other than the programmed brightness will cause the Motion Dimmer to be disabled for the amount of time specified in “Manual Override Time”. Changes in color do not disable the motion dimmer.  This allows the dimmer to work in conjunction with integrations that adjust the color temperature of the light over time.  Set this to 0 if you do not want the Motion Dimmer to be disabled automatically.
- `Disabled Until:`  When a Motion Dimmer is manually overridden, the “Disabled Until” datetime is set to the future.  The Motion Dimmer will not activate until after that time.  You can manually set this time if you want the dimmer to be deactivated temporarily.
- `Trigger Test Interval:`  When you trigger a Motion Dimmer it will periodically poll the trigger to see if it is still on.  If so it will reset the time and add a little bit more to it.  The “Trigger Test Interval” should be set to a number greater than the motion sensor timeout so it can determine if the motion sensor is still detecting motion.  This way you can set the initial “[dropdown item] Seconds” to a smaller number and trust that the Motion Dimmer will keep the light on until there is no motion in the room.  Set this number to 0 if you don’t want the Motion Dimmer to restart the timer.  Each time the trigger turns on, the Motion Dimmer will still restart the time even without a test interval.
- `Max Extension:`  This is the maximum number that the Motion Dimmer can add to the original timer.  Set this to a low number in rooms that have high traffic and low continuous activity like hallways.  Set this number higher in rooms that have long activity times but intervals of little motion like TV rooms.  Set this number to 0 if you want the dimmer to only be on for the specified amount of time.
- `Prediction Time:`  Often when you enter a room with a motion sensor the light doesn’t turn on until you are well within the room.  If you have motion sensors in adjacent rooms you can set them as predictors.  When a predictor is activated the light is turned on to the brightness set for the amount of time set.  If configured correctly, you will never have to enter a dark room again.
- `Prediction Brightness:`  You might set this to a low brightness that just illuminates the room.  If you activate the trigger, the Motion Dimmer will turn on to full brightness.  If you don't, it will turn back off after a short time.
- `Minimum brightness:`  Some dimmers won’t turn on if you go from off to 1%, but they will work if you start from a higher number.  Minimum brightness is the percent that the light needs to activate before being lowered to the desired brightness.  If the Motion Dimmer is set to a brightness that is lower than the minimum brightness, the light will first turn on at the minimum number for 1 second and then be lowered.

Note, all of these entities can be manipulated with automations and scenes to add more sophisticated functionality.  Adding these entities to groups can allow for convenient dashboards, as well.

Motion Dimmer also provides a sensor which tracks the timer.  The state is either “Active” or “Idle” and it has two attributes: `timer_end` and `timer_seconds`.  This can be used in conjunction with integrations like “Timer Bar Card” to display a countdown timer in dashboards.

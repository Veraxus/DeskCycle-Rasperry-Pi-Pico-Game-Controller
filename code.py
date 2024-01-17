"""
File Name: code.py
Author: Dutch van Andel
Date: 2024-01-16
Description:
    This determines the direction and speed of a stationary bike that contains
    two (2) hall sensors placed about 3mm apart and 8 total magnets.
"""
import time
import board
import analogio
import digitalio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# == SETTINGS ===========================================

# -- debug --
debug = 0  # 1 = enable debug output, 2 = verbose debug output, 3 = very verbose
disable_keyboard = 0  # If true, disables keypresses

# -- sensor calibration --
analog_threshold = 34100  # At what point does the sensor trigger a true?

# -- Resistance Level 3 w/ 8 magnets--
min_timeout = 0.191  # (Seconds) The lowest avg interval time before stop is assumed
max_timeout = 0.38  # (Seconds) The highest avg interval time before stop is assumed
stop_smoothing = 4  # (Int) The number of intervals to check against when calculating stop
stop_smoothing_scale = 0.01  # The most a smoothed interval value is allowed to change in one interval

sprint_start = 0.072  # (Seconds) Interval where sprint starts
sprint_end = 0.12  # (Seconds) Interval where sprint ends
sprint_smoothing = 5  # (Int) The number of intervals to check against when calculating sprint start/stop

# -- Game-specific --
disable_sprint = 0  # Set to true to disable sprint functionality


# == INITIALIZE BOARD FEATURES ==========================

# Bottom switch output (near switch / socket output)
hall1 = analogio.AnalogIn(board.GP26) # ADC0 - row 10 right - grey

# Bottom switch output (near switch / socket output)
hall2 = analogio.AnalogIn(board.GP27)  # ADC1 - row 11 right - white

# Enable/disable button
button = digitalio.DigitalInOut(board.GP10)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.DOWN

# Start with input enabled
button_state = True
last_button = button.value

# Onboard LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Virtual keyboard output over USB
keyboard = Keyboard(usb_hid.devices)

# What was the last single sensor to be triggered?
last_switch = None

# The interval timestamps for the last X intervals
interval_history = []
max_history = max(stop_smoothing, sprint_smoothing) + 1

# Tracks the last time activity was detected
last_activity = time.monotonic()
inactive_count = 1

# Allows min_timeout to start with first interval number and decrease over time
smoothed_min_timeout_interval = False

# Set by switch transit to limit certain actions
actions_ready = False

# What keys are currently being pressed
active_keys = set()

# Create a dictionary for converting keycodes back to key names
keydict = {value: name for name, value in Keycode.__dict__.items() if isinstance(value, int)}


# == Functions ==========================================

def press_key(keycode):
    """
    Press a key, add to key state, print debug msg

    Args:
        keycode (int): A keycode for key being pressed
    """
    global debug, keyboard, active_keys

    # Press & track the key
    if keycode not in active_keys:
        if debug:
            print(f"{time.monotonic()} Pressed {keydict[keycode]}")
        active_keys.add(keycode)

    # Always force the press, since using WSAD on a different keyboard can supercede cycle input
    if not disable_keyboard:
        keyboard.press(keycode)


def release_key(keycode):
    """
    Release a key, discard from key state, print debug msg

    Args:
        keycode (int): A keycode for key being released
    """
    global debug, keyboard, active_keys

    # UNpress the key
    if keycode in active_keys:
        if debug:
            print(f"{time.monotonic()} Released {keydict[keycode]}")
        active_keys.discard(keycode)

        if not disable_keyboard:
            keyboard.release(keycode)


def release_all_keys():
    """
    Release all keyboard keys
    """
    global debug, keyboard, active_keys

    # Debug message
    if debug:
        keys_str = [keydict[key] for key in active_keys if key in keydict]
        print(f"{time.monotonic()} Released all keys: {keys_str}")

    # Release the keys
    keyboard.release_all()

    # Track key releases
    active_keys.clear()


def get_interval_avg_sprint(max_len, current_time):
    """
    Get the average value of the last x history items

    Args:
        max_len (int): The maximum number of items to check
    """
    if len(interval_history):
        max_len = min(max_len, len(interval_history))
        items = interval_history[-max_len:]
        items.append(current_time)
        # Convert monotonic times to intervals
        intervals = [items[i] - items[i - 1] for i in range(1, len(items))]
        # Calc the average
        avgs = sum(intervals) / len(intervals)
        return avgs
    return 0


def full_stop():
    """
    Reset state to a complete stop
    """
    global smoothed_min_timeout_interval
    release_all_keys()
    interval_history.clear()
    # Reset smoothed interval for next motion start
    smoothed_min_timeout_interval = False


def analog_bool(sensor_value):
    """
    Determine if the hall sensor is detecting a magnet. Output is between 0 and 65,536.
    The default for the 49E/273BD sensors at 3.3V is about 32,500. Exposing the front side
    of the sensor to a strong neodymium magnet at ~1/2" increases this to 36,000 and a weak
    magnet to about 34,000 and 1/4".
    Args:
        sensor_value (int): The analog value of the sensor.

    Returns (bool):
        True if the sensor exceeds the threshold, otherwise false
    """
    if not sensor_value:
        return False
    else:
        if debug >= 4:
            print(f"{sensor_value} >= {analog_threshold} | {sensor_value >= analog_threshold}")
        return sensor_value >= analog_threshold

# == THE LOOP ===========================================

led_history = []

print("Initialized")
if debug:
    print(f"Debug level {debug}")
while True:
    ctime = time.monotonic()
    switch1 = analog_bool(hall1.value)
    switch2 = analog_bool(hall2.value)
    both_sw = switch1 and switch2
    either_sw = switch1 or switch2
    
    # Process the disable button
    if button.value != last_button:
        last_button = button.value
        if not button.value:
            button_state = not button_state
            if button_state:
                print('Enabled input.')
                disable_keyboard = False
                led.value = False
            else:
                print('Disabled input.')
                disable_keyboard = True
                led.value = True
            
    # Blink when both switches are activated at once
    led.value = both_sw

    # Idle notice (useful for debugging)
    if last_activity and ctime - last_activity > 5 and inactive_count <= 360:
        print("{} No motion detected for over {} seconds.".format(ctime, 5 * inactive_count))
        last_activity = ctime
        inactive_count += 1

    # Begin sensor-detection logic
    if either_sw and not both_sw:
        last_switch = 1 if switch1 else 2
        if debug >= 4:
            print(f"{ctime} One switch active: {last_switch}")

    if both_sw:
        actions_ready = True
        if debug >= 4:
            print(f"{ctime} Both switches active. Actions enabled.")

    # == Ended Sensor Reads - Perform Actions ===========
    elif actions_ready and not either_sw:

        # Reset action tracking vars
        actions_ready = False
        inactive_count = 1

        if debug >= 3:
            print(f"{ctime} Processing actions!")

        # == Determine Direction ========================

        # Forward - exited sw2 last
        if last_switch == 2:
            release_key(Keycode.S)
            press_key(Keycode.W)
        # Backward - exited sw1 last
        elif last_switch == 1:
            release_key(Keycode.W)
            press_key(Keycode.S)

        if len(interval_history):

            if debug >= 3:
                print(f"{ctime} Interval history is {len(interval_history)}, processing direction.")

            # == Determine Speed =============================

            # Get average of saved history for sprint
            interval_avg_sprint = get_interval_avg_sprint(sprint_smoothing, ctime)

            if debug >= 2:
                print(f"{ctime} Interval average: {interval_avg_sprint}")

            # Calculate sprinting
            if not disable_sprint:
                if interval_avg_sprint <= sprint_start:
                    if debug >= 1 and Keycode.SHIFT not in active_keys:
                        print(f"{ctime} Sprint started. ===================> 🏃")
                    press_key(Keycode.SHIFT)
                elif interval_avg_sprint >= sprint_end:
                    if debug >= 1 and Keycode.SHIFT in active_keys:
                        print(f"{ctime} Sprint ended. XXXXXXXXXXXXXXXXXXXXXX 🏃")
                    release_key(Keycode.SHIFT)
                        
            # Get average of saved history for stop
            interval_avg_stop = get_interval_avg_sprint(stop_smoothing,ctime)

            # Set initial smooth min_timeout
            if not smoothed_min_timeout_interval:
                # Smoothed timeout is the higher of current or max
                smoothed_min_timeout_interval = max(interval_avg_stop, max_timeout)
                if debug >= 2:
                    print(f"{ctime} Smoothed timeout interval: {smoothed_min_timeout_interval}")

            # If last interval is higher than current one...
            else:
                if smoothed_min_timeout_interval > interval_avg_stop:
                    # And current interval is still longer than the min_timeout...
                    if interval_avg_stop >= min_timeout:
                        # Then use current interval as latest (decreases naturally)
                        if debug >= 2:
                            print(f"{ctime} Lowering min_timeout from {smoothed_min_timeout_interval} to {max(interval_avg_stop,smoothed_min_timeout_interval - stop_smoothing_scale)}")
                        smoothed_min_timeout_interval = max(interval_avg_stop, smoothed_min_timeout_interval - stop_smoothing_scale)

                    # Otherwise, don't go below the min_timeout
                    else:
                        if debug >= 2 and smoothed_min_timeout_interval != min_timeout:
                            print(f"{ctime} Reached minimum min_timeout {min_timeout}")

                        smoothed_min_timeout_interval = min_timeout

                    if debug >= 2 and smoothed_min_timeout_interval != min_timeout:
                        print(f"{ctime} Smooth min_timeout: {smoothed_min_timeout_interval}")

        # Record latest interval
        interval_history.append(ctime)
        last_activity = ctime

    # == Determine If Stopped ===========================
    # Get the average intervals within stop smoothing scope
    stop_avg = get_interval_avg_sprint(stop_smoothing, ctime)
    
    # If the average interval is higher than the calculated stop interval....
    if ((smoothed_min_timeout_interval and stop_avg > smoothed_min_timeout_interval)
            or (last_activity and ctime - last_activity > max_timeout)):
        if len(active_keys):
            if debug >= 2:
                print(f"{ctime} Stop detected! Calculation: ({smoothed_min_timeout_interval} and {stop_avg} > {smoothed_min_timeout_interval}) or ({last_activity} and {ctime - last_activity} > {max_timeout}) ")
            full_stop()

    # == Cleanup/Memory Mgmt ============================
    # Prune the history
    if len(interval_history) > max_history:
        interval_history = interval_history[-max_history:]

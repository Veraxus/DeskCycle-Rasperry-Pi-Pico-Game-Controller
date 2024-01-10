"""
File Name: code.py
Author: Dutch van Andel
Date: 2024-01-09
Description:
    This determines the direction and speed of a stationary bike that contains two reed sensors (at approx 75 degrees
    from the main wheel) and two magnets attached to the wheel.
"""
import time
import board
import digitalio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# == CONFIG VALUES ======================================

debug = False  # 1 = minimal debug, 2 = detailed info, 3 = exhaustive info

pedal_sprint_rate = 0.15  # Seconds per interval for sprinting
pedal_timeout = 0.8  # Seconds without a switch activation before a full stop is assumed

debounce_time = 0.05  # Delays for switch activation checks since reed switched bounce
loop_wait_time = 0.01  # Delay in the main loop to conserve power

min_history_length = 2  # The minimum number of transitions to remember for each path before making calculations
max_history_length = 4  # The max number of transitions to remember for each path

# == INITIALIZE BOARD FEATURES ==========================

# Top switch output (far switch / pin output)
input_top = digitalio.DigitalInOut(board.GP16)
input_top.direction = digitalio.Direction.INPUT
input_top.pull = digitalio.Pull.DOWN

# Bottom switch output (near switch / socket output)
input_bottom = digitalio.DigitalInOut(board.GP18)
input_bottom.direction = digitalio.Direction.INPUT
input_bottom.pull = digitalio.Pull.DOWN

# Onboard LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Virtual keyboard output over USB
keyboard = Keyboard(usb_hid.devices)

# Create a dictionary for converting keycodes back to key names
keydict = {value: name for name, value in Keycode.__dict__.items() if isinstance(value, int)}

# == GLOBAL STATE =======================================

# Time of last switch activation
far_switch_ltime = 0
near_switch_ltime = 0

# Tracking whether a switch was activated
far_switch_enabled = False
near_switch_enabled = False

# What was the last switch that turned off?
last_switch = None

# Which way is the wheel turning? (0=stopped, 1=forward, 2=reverse)
rotation_direction = 0

# For faster identification of direction changes
flip_direction = False

# Track the intervals between switch activations
far_to_near_intervals = []
near_to_far_intervals = []

# What keys are currently being pressed
active_keys = set()


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
        print(f"Pressed " + keydict[keycode])
        active_keys.add(keycode)
        if not debug:
            keyboard.press(keycode)


def release_key(keycode):
    """
    Release a key, discard from key state, print debug msg

    Args:
        keycode (int): A keycode for key being released
    """
    global debug, keyboard, active_keys

    # Press the key
    if keycode in active_keys:
        print(f"Released " + keydict[keycode])
        if not debug:
            keyboard.release(keycode)

    # Track key releases
    active_keys.discard(keycode)


def release_all_keys():
    """
    Release all keyboard keys
    """
    global debug, keyboard, active_keys

    # Press the key
    if not debug:
        keyboard.release_all()

    # Track key releases
    active_keys.clear()

    # Debug message
    print(f"Released all keys")


# == START LOOP =========================================

while True:
    current_time = time.monotonic()

    # == READ SWITCH STATES =============================

    # Whether to process switch logic (happens only once as soon as a switch turns off)
    ready_for_actions = False

    # Is a switch CURRENTLY active (with debounce)
    far_switch_is_live = input_top.value and (current_time - far_switch_ltime > debounce_time)
    near_switch_is_live = input_bottom.value and (current_time - near_switch_ltime > debounce_time)

    # Debug: Turn on LED if any switch is active
    led.value = far_switch_is_live or near_switch_is_live

    # Enable switches for future action
    if far_switch_is_live:
        far_switch_enabled = True
    if near_switch_is_live:
        near_switch_enabled = True

    # == SWITCH TRIGGER LOGIC ===========================

    # Switch just turned off, handle switch logic
    if far_switch_enabled and not far_switch_is_live:
        # Track interval since the other switch
        if last_switch == 'NEAR':
            near_to_far_intervals.append(current_time - near_switch_ltime)

            # Keep history pruned to max
            if len(near_to_far_intervals) > max_history_length:
                near_to_far_intervals.pop(0)

        # The same switch hit twice means a change in direction
        elif last_switch == 'FAR':
            flip_direction = True

        # Set vars
        far_switch_ltime = current_time
        last_switch = 'FAR'
        far_switch_enabled = False
        ready_for_actions = True
        if debug == 3:
            print('-- FAR')

    elif near_switch_enabled and not near_switch_is_live:
        # Track interval since the other switch
        if last_switch == 'FAR':
            far_to_near_intervals.append(current_time - far_switch_ltime)

            # Keep history pruned to max
            if len(far_to_near_intervals) > max_history_length:
                far_to_near_intervals.pop(0)

        # The same switch hit twice means a change in direction
        elif last_switch == 'NEAR':
            flip_direction = True

        # Set vars
        near_switch_ltime = current_time
        last_switch = 'NEAR'
        near_switch_enabled = False
        ready_for_actions = True
        if debug == 3:
            print('–– NEAR')

    # todo: Same switch hit twice? Reverse direction.

    # == CALCULATE DIRECTION ============================

    # Ready to handle switch-related actions
    if ready_for_actions:

        # If we already know the direction but flip was detected, reverse fresh
        if rotation_direction and flip_direction:
            rotation_direction = 2 if rotation_direction == 1 else 1
            flip_direction = False
            far_to_near_intervals.clear()
            near_to_far_intervals.clear()
            print('() Flipping direction')

        # Is there enough history to calculate direction?
        elif (len(far_to_near_intervals) >= min_history_length
              and len(near_to_far_intervals) >= min_history_length):

            # Calculate averages for each path
            avg_far_to_near = sum(far_to_near_intervals) / len(far_to_near_intervals)
            avg_near_to_far = sum(near_to_far_intervals) / len(near_to_far_intervals)

            if debug == 2:
                print(f"f2n avg: {avg_far_to_near}")
                print(' ')
                print(f"n2f avg: {avg_near_to_far}")

            # The shorter path tells us the direction
            # Note: The values are consistently backwards and I don't know why. Oh well, I will accept the consistency.
            if avg_near_to_far < avg_far_to_near:
                rotation_direction = 2
                if debug == 2:
                    print('<== Backward')
            else:
                rotation_direction = 1
                if debug == 2:
                    print('Forward ==>')
                # Hold shift to sprint?
                if avg_far_to_near < pedal_sprint_rate:
                    press_key(Keycode.SHIFT)
                else:
                    release_key(Keycode.SHIFT)

        # Press the appropriate keys!
        if rotation_direction == 1:
            release_key(Keycode.S)
            press_key(Keycode.W)
        elif rotation_direction == 2:
            release_key(Keycode.W)
            press_key(Keycode.S)

    # Detect stoppage
    if (rotation_direction
            and current_time > far_switch_ltime + pedal_timeout
            and current_time > near_switch_ltime + pedal_timeout):
        print('Stopped')
        rotation_direction = 0
        far_switch_ltime = 0
        near_switch_ltime = 0
        last_switch = None
        far_to_near_intervals = []
        near_to_far_intervals = []
        release_all_keys()

    # Slow down the loop
    time.sleep(loop_wait_time)

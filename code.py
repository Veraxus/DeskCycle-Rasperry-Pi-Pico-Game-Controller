"""
File Name: code.py
Author: Dutch van Andel
Date: 2024-01-13
Description:
    This determines the direction and speed of a stationary bike that contains
    two (2) hall sensors placed about 3mm apart and 1 or more magnets.
"""
import time
import board
import digitalio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# == SETTINGS ===========================================

# -- Resistance Level 3 --
timeout = 0.40  # (Seconds) Maximum avg interval time before stop is assumed
sprint_start = 0.16  # (Seconds) Interval where sprint starts
sprint_end = 0.18  # (Seconds) Interval where sprint ends
sprint_smoothing = 3  # (Int) The number of intervals to check against when calculating sprint
stop_smoothing = 2  # (Int) The number of intervals to check against when calculating stop
debug = 1  # 1 = enable debug output, 2 = also disable keypresses

# == INITIALIZE BOARD FEATURES ==========================

# Bottom switch output (near switch / socket output)
hall1 = digitalio.DigitalInOut(board.GP15)
hall1.direction = digitalio.Direction.INPUT
hall1.pull = digitalio.Pull.UP

# Bottom switch output (near switch / socket output)
hall2 = digitalio.DigitalInOut(board.GP16)
hall2.direction = digitalio.Direction.INPUT
hall2.pull = digitalio.Pull.UP

# Onboard LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Virtual keyboard output over USB
keyboard = Keyboard(usb_hid.devices)

# What was the last single sensor to be triggered?
last_switch = None

# The interval timestamps for the last X intervals
interval_history = []
max_history = max(stop_smoothing, sprint_smoothing)

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
            print(f"{time.monotonic()} Pressed " + keydict[keycode])
        active_keys.add(keycode)
        if not debug or debug < 2:
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
            print(f"{time.monotonic()} Released " + keydict[keycode])
        active_keys.discard(keycode)
        
        if not debug or debug < 2:
            keyboard.release(keycode)


def release_all_keys():
    """
    Release all keyboard keys
    """
    global debug, keyboard, active_keys

    # Press the key
    keyboard.release_all()

    # Track key releases
    active_keys.clear()

    # Debug message
    if debug:
        print(f"{time.monotonic()} Released all keys")

def get_interval_avg(max_len, current_time):
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

while True:
    ctime = time.monotonic()
    switch1 = not hall1.value
    switch2 = not hall2.value
    bothsw = switch1 and switch2
    eithersw = switch1 or switch2
    
    led.value = bothsw
    
    if eithersw and not bothsw:
        last_switch = 1 if switch1 else 2
    
    if bothsw:
        actions_ready = True
        if last_switch == 1:
            release_key(Keycode.S)
            press_key(Keycode.W)
            
        else:
            release_key(Keycode.W)
            press_key(Keycode.S)
            
    elif actions_ready and not eithersw:
        actions_ready = False
        if len(interval_history):
            
            # Get average of saved history
            interval_avg = get_interval_avg(sprint_smoothing, ctime)
            
            if debug:
                print(f"{time.monotonic()} Last avg: {interval_avg}")
            
            # Calculate sprinting
            if interval_avg <= sprint_start:
                press_key(Keycode.SHIFT)
            elif interval_avg >= sprint_end:
                release_key(Keycode.SHIFT)
                
        # Record latest interval
        interval_history.append(ctime)
        
    # Determine stop
    stop_avg = get_interval_avg(stop_smoothing, ctime)
    if stop_avg > timeout:
        
        if len(active_keys):
            release_all_keys()
            
    # Prune the history
    if len(interval_history) > max_history:
        interval_history = interval_history[-max_history:]
        


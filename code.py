import time
import board
import digitalio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# Thresholds
pedal_sprint_rate = 0.5  # Seconds per revolution threshold for fast pedaling
pedal_stop_timeout = 1.5 # Timeout for no pedaling detection
debounce_time = 0.05     # Delays for switch activation checks since reed switched bounce
loop_wait_time = 0.01    # Delay in the main loop to conserve power

# Initialize keyboard
keyboard = Keyboard(usb_hid.devices)

# Setup the DeskCycle's reed switches
switch1 = digitalio.DigitalInOut(board.GP16)
switch1.direction = digitalio.Direction.INPUT
switch1.pull = digitalio.Pull.DOWN

switch2 = digitalio.DigitalInOut(board.GP17)
switch2.direction = digitalio.Direction.INPUT
switch2.pull = digitalio.Pull.DOWN

# Setup onboard LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Track which switch was the LAST to be triggered
last_switch1 = False
last_switch2 = False

# Pedaling direction: True for forward, False for backward, None for stopped/unknown
pedaling_forward = None

# Tracks the time the most recent switch was triggered
last_switch_time = 0

# Track which keypresses are active
active_keys = set()

# Main loop
while True:
    current_time = time.monotonic()
    
    # Debounce-corrected switch activation check
    switch1_active = switch1.value and (current_time - last_switch_time > debounce_time)
    switch2_active = switch2.value and (current_time - last_switch_time > debounce_time)

    # Debug: Turn on LED if any switch is active
    led.value = switch1_active or switch2_active

    # Determine forward/backward based on the order in which switches are triggered
    if switch1_active and not last_switch1:
        
        # If switch2 was active last, we are pedalling backward
        if last_switch2:
            pedaling_forward = False
            print("S1A: Detected backward pedaling")
        # Going forward (likely from a stop)
        else:
            pedaling_forward = True
            print("S1A: Detected forward pedaling from stop")
        last_switch_time = current_time


    elif switch2_active and not last_switch2:
        # If switch1 was active last, we are pedalling forward
        if last_switch1:
            pedaling_forward = True
            print("S2A: Detected forward pedaling")
        # Going backward (likely from a stop)
        else:
            pedaling_forward = False
            print("S2A: Detected backward pedaling from stop")
        last_switch_time = current_time

    # Translate detected movement into keyboard input
    if pedaling_forward is not None:
        
        # Walking forward
        if pedaling_forward and not Keycode.W in active_keys:
            keyboard.release(Keycode.S)
            active_keys.discard(Keycode.S)
            keyboard.press(Keycode.W)
            active_keys.add(Keycode.W)
            print("Pressed W key")
        # Walking backward
        elif not pedaling_forward and not Keycode.S in active_keys:
            keyboard.release(Keycode.W)
            active_keys.discard(Keycode.W)
            keyboard.press(Keycode.S)
            active_keys.add(Keycode.S)
            print("Pressed S key")

        # Initiate sprinting (hold down SHIFT)
        if current_time - last_switch_time <= pedal_sprint_rate and not Keycode.SHIFT in active_keys:
            keyboard.press(Keycode.SHIFT)
            active_keys.add(Keycode.SHIFT)
            print("Pressed SHIFT key")
        # Stop sprinting (release SHIFT)
        elif current_time - last_switch_time > pedal_sprint_rate and Keycode.SHIFT in active_keys:
            keyboard.release(Keycode.SHIFT)
            active_keys.discard(Keycode.SHIFT)
            print("Released SHIFT key")
    
    # Wheel is not moving, release all keys
    elif active_keys:
            keyboard.release_all()
            active_keys.clear()
            print("DeskCycle is inactive.")

    # Detect when pedalling stops and release all keys
    if current_time - last_switch_time >= pedal_stop_timeout and active_keys:
        keyboard.release_all()
        active_keys.clear()
        pedaling_forward = None
        print("Pedaling stopped, released all keys.")

    # Update last switch states
    last_switch1 = switch1_active
    last_switch2 = switch2_active

    # Debounce
    time.sleep(loop_wait_time)

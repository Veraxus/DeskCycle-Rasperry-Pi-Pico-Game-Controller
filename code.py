import time
import board
import digitalio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode


# Settings in SPR (Seconds Per Revolution)
run_speed = 0.99 # Anything lower adds SHIFT
stop_speed = 1.6 # Anything slower unpresses keys


# Setup keyboard
keyboard = Keyboard(usb_hid.devices)


# Setup switch input
cycle = digitalio.DigitalInOut(board.GP28)
cycle.direction = digitalio.Direction.INPUT
cycle.pull = digitalio.Pull.DOWN


# Track last loop time
trigger_active = False
trigger_time = time.monotonic()


# Track keys
holdingW = False
holdingSHIFT = False


while True:
    loop_time = time.monotonic()
    rev_time = loop_time - trigger_time
    
    
    # Circuit closed!
    if cycle.value:
        trigger_active = True
        
        
    # Circuit broken! Start actions.
    elif trigger_active == True:
        trigger_active = False
        trigger_time = loop_time
        
        if not holdingSHIFT and rev_time <= run_speed:
            holdingSHIFT = True
            keyboard.press(Keycode.SHIFT)
            print("Hold SHIFT")
            
        if not holdingW:
            holdingW = True
            keyboard.press(Keycode.W)
            print("Hold W")
            
        print("    Rev time = " + str(rev_time))
        
      
    # Timeout - full stop
    if holdingW and rev_time >= stop_speed:
        keyboard.release_all()
        holdingW = False
        holdingSHIFT = False
        print("Stop All")
        print("    Rev time = " + str(rev_time))
        
    # Timeout - stop running
    if holdingSHIFT and rev_time > run_speed:
        keyboard.release(Keycode.SHIFT)
        holdingSHIFT = False
        print("Stop SHIFT")
        print("    Rev time = " + str(rev_time))


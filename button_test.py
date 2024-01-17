import time
import board
import digitalio
import analogio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

debug = 0

button = digitalio.DigitalInOut(board.GP10)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.DOWN
button_state = False
last_button = button.value

# Onboard LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT
led.value = False

def log(msg, level = 1):
    if debug >= level:
        print(f"{time.monotonic()}: {msg}")

print('Initialized!')

while True:
    led.value = button_state
    
    if button.value != last_button:
        last_button = button.value
        if not button.value:
            button_state = not button_state



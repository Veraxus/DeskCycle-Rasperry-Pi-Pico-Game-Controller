"""
File Name: test.py
Author: Dutch van Andel
Date: 2024-01-15
Description:
    A small script for testing hall sensors via analog inputs.
"""
import time
import board
import digitalio
import analogio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

debug = 0

hall1 = analogio.AnalogIn(board.GP26) # ADC0 - row 10 right - grey
hall2 = analogio.AnalogIn(board.GP27)  # ADC1 - row 11 right - white

# Onboard LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT
led.value = False

def log(msg, level = 1):
    if debug >= level:
        print(f"{time.monotonic()}: {msg}")

print('Initialized!')

while True:
    log(f"Grey {hall2.value} {hall2.value >= 34100}| White {hall1.value} {hall1.value >= 34100}", 0)
    
    if (hall2.value >= 34100 and hall1.value >= 34100):
        print('========= TRUE ===========')
    
    time.sleep(0.5)


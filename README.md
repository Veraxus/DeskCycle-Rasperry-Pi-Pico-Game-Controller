# DeskCycle-Game-Controller
Use a Raspberry Pi Pico to convert your pedaling speed into WSAD game movement.

## Requirements
Assumes use of CircuitPython for your Pico ( https://circuitpython.org/board/raspberry_pi_pico/ ) or Pico W ( https://circuitpython.org/board/raspberry_pi_pico_w/ ) microcontroller.

You will also need the Adafruit CircuitPython HID bundle ( https://github.com/adafruit/Adafruit_CircuitPython_HID )

## Wiring
Use a 3.5mm cable extender. Plug one end into the 3.5mm connector coming out of the Cycle. 

Next, either use a 3.5mm jack or cut the other end of the cable and separate the internal cables.

Connect the ground wire to grnd, and then one of the two wires to 3V3 out and the other to GP27 (if you want to use a different pin, you can change it in code.py).

That's it!

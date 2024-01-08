# DeskCycle-Game-Controller
Use a Raspberry Pi Pico to convert your DeskCycle pedaling speed into WSAD game movement.

## Requirements
Assumes use of CircuitPython for your Pico ( https://circuitpython.org/board/raspberry_pi_pico/ ) or Pico W ( https://circuitpython.org/board/raspberry_pi_pico_w/ ) microcontroller.

You will also need the Adafruit CircuitPython HID bundle ( https://github.com/adafruit/Adafruit_CircuitPython_HID )

## Wiring
Use a 3.5mm cable extender. Plug one end into the 3.5mm connector coming out of the Cycle. 

Next, either use a 3.5mm jack with your Pico for a clean, modular connection, or cut the other end of the 3.5mm cable and separate the internal cables.

Connect the ground wire to grnd, and then one of the two wires to 3V3 out and the other to GP27 (if you want to use a different pin, you can change it in code.py).

That's it!

## Notes
The DeskCycle creates a switch connection once per revolution for RPM monitoring. We simply use that to control when the 'W' key is held down or, when the time between rotations is short enough, the "Shift" key as well. 

Because there is only 1 switch in the rotation, the responsiveness (both start and stop) can feel a little sluggish. I'll need to open up the DeskCycle and see how the switch is triggered. With a little luck (I'm hoping it's just a magnetic switch attached to the gear), it may be possible to add more frequent switching, which would allow us to improve the responsiveness.

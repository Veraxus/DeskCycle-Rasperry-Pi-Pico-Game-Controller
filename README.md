# DeskCycle-Game-Controller
Use a Raspberry Pi Pico to convert your DeskCycle pedaling speed into WSAD game movement.

## Requirements
Assumes use of CircuitPython for your Pico ( https://circuitpython.org/board/raspberry_pi_pico/ ) or Pico W ( https://circuitpython.org/board/raspberry_pi_pico_w/ ) microcontroller.

You will also need the Adafruit CircuitPython HID bundle ( https://github.com/adafruit/Adafruit_CircuitPython_HID )

This version of the code assumes the cycle has been customized with 2 new hall sensors placed approx 3mm apart, and that wheel has had 4 magnets installed. The hall sensors need to be close enough that they both activate when one magnet is between them, but far enough that one can still activate before the other.

## Wiring
Either splice the wires from one end of a 3.5mm cable onto each hall sensor (recommend tip for out, ring1 for current, and sleeve for ground), or (what I recommend) solder the sensors to a 3.5mm jack so the cables can be easily replaced in the future.

## Explanation
The placement of the default switches inside the DeskCycle mean that they are effectively (though not literally) positioned at a 90 degree angle from one another. While we can use only two magnets (placed at 180 degrees) and use timing logic to determine wheel direction, it results in less than ideal responsiveness. Four magnets will not work with the default switches, however.

This implementation uses hall sensors placed much closer together. This allows the magnet to either trigger one, then both at the same time. When both are triggered at the same time, we can easily tell which direction the wheel turned with a high degree of precision and responsiveness based purely on which of the two was triggered first. This approach also works for four (or even more, if you were so inclined) magnets, which further improves responsiveness.
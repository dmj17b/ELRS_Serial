# Python ELRS Serial Parsing Library

## Overview:
This code is meant to read a serial port (in this case, the TX/RX pins on a Raspberry Pi) and parse the different information coming to/from the RC transmitter.

Ensure that the TX pin of ELRS receiver is connected to RX of RPi, and vice-versa. Also ensure 5V and ground are connected to properly power the receiver.

If the receiver is not bound, quickly power cycle it 3 times and the indicator light should flash to let user know that it is in "bind" mode. You can select the "bind" option on the transmitter to finish binding. Once bound, the receiver should show a solid green light.

If the receiver has been bound, but is not connected (for whatever reason) ensure the transmitter is powered on and the correct model is selected, then power cycle the receiver ONCE to reconnect.
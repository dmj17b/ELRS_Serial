# Python ELRS Serial Parsing Library

## NOTE:
Seeing that some people are starting to star this repository for use, I figured it was important to let everyone know that most of this code was written by ClaudeAI just to get the problem solved. For my purposes it works, and I have tested it on hardware, but little is optimized. If anyone would like to contribute and improve this ELRS parser, it would be greatly appreciated. I could not find any similar python ELRS parsers, so I hope the community can benefit from this.

## Overview:
This code is meant to read a serial port (in this case, the TX/RX pins on a Raspberry Pi) and parse the different information coming to/from the RC transmitter.

Ensure that the TX pin of ELRS receiver is connected to RX of RPi, and vice-versa. Also ensure 5V and ground are connected to properly power the receiver.

If the receiver is not bound, quickly power cycle it 3 times and the indicator light should flash to let user know that it is in "bind" mode. You can select the "bind" option on the transmitter to finish binding. Once bound, the receiver should show a solid green light. 

If the receiver has been bound, but is not connected (for whatever reason) ensure the transmitter is powered on and the correct model is selected, then power cycle the receiver ONCE to reconnect.

In future commits, I hope to find a way to "force" the receiver into bind mode when the Pi is powered on. Currently the receiver only binds after the Pi has booted up and I manually power cycle the receiver. I imagine there is some sort of message I can send to quick-reset the receiver so that it connects at the start of each control script. Again, I am happy to have anyone contribute to help solve some of these issues.

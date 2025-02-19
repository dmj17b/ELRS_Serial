import time
import ELRS2 as rx
# Initialize receiver
receiver = rx.CRSFReceiver(port='/dev/ttyS0', baudrate=420000)

# Example voltage value (you can replace this with real sensor data)
battery_voltage = 11.8  # volts

try:
    while True:
        # Update receiver data
        receiver.update()
        
        # # Send battery telemetry
        # receiver.send_battery_telemetry(
        #     voltage=battery_voltage,
        #     current=0.0,            # Optional: current in amps
        #     mah=0,                  # Optional: consumed capacity
        #     remaining_percent=100    # Optional: battery percentage
        # )
        
        # Get channel values (if needed)
        channels = receiver.get_channels()
        for i in range(1,16):
            print(f"Channel: {i} Val: {channels[i]}")        
    
        # Get link statistics (if needed)
        if receiver.link_stats is not None:
            link_stats = receiver.get_link_stats()
            print(f"RSSI1: {link_stats.rssi1} dBm")
            print(f"RSSI2: {link_stats.rssi2} dBm")
            print(f"Link quality: {link_stats.link_quality}%")
            print(f"SNR: {link_stats.snr} dB")


except KeyboardInterrupt:
    receiver.close()
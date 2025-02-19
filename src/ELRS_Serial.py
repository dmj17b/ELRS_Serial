import serial
import time
from enum import IntEnum
from typing import Dict, Optional, List
from dataclasses import dataclass
import struct

@dataclass
class LinkStats:
    rssi1: int
    rssi2: int
    link_quality: int
    snr: int

class CRSFReceiver:
    """
    Library for reading CRSF receiver data and sending telemetry.
    """
    
    CRSF_SYNC = 0xC8
    CRSF_TELEMETRY_SYNC = 0xC8
    
    class PacketTypes(IntEnum):
        GPS = 0x02
        VARIO = 0x07
        BATTERY_SENSOR = 0x08
        BARO_ALT = 0x09
        HEARTBEAT = 0x0B
        VIDEO_TRANSMITTER = 0x0F
        LINK_STATISTICS = 0x14
        RC_CHANNELS_PACKED = 0x16
        ATTITUDE = 0x1E
        FLIGHT_MODE = 0x21
        DEVICE_INFO = 0x29
    
    def __init__(self, port: str = '/dev/ttyS0', baudrate: int = 420000):
        """
        Initialize CRSF receiver.
        
        Args:
            port: Serial port path
            baudrate: Serial baudrate (default: 420000 for ELRS)
        """
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.input_buffer = bytearray()
        
        # Store latest received data
        self.channels: Dict[int, int] = {i: 1500 for i in range(1, 17)}
        self.link_stats: Optional[LinkStats] = None
        
        self._connect()
    
    def _connect(self):
        """Establish serial connection."""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
        except serial.SerialException as e:
            raise ConnectionError(f"Failed to connect to {self.port}: {e}")
    
    def _crc8_dvb_s2(self, crc: int, a: int) -> int:
        """Calculate CRC8 DVB-S2 for a byte."""
        crc = crc ^ a
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0xD5
            else:
                crc = crc << 1
        return crc & 0xFF
    
    def _crc8_data(self, data: bytes) -> int:
        """Calculate CRC8 DVB-S2 for a sequence of bytes."""
        crc = 0
        for a in data:
            crc = self._crc8_dvb_s2(crc, a)
        return crc
    
    def _validate_frame(self, frame: bytes) -> bool:
        """Validate CRSF frame using CRC8."""
        return self._crc8_data(frame[2:-1]) == frame[-1]
    
    def _decode_channels(self, data: bytes) -> None:
        """Decode CRSF RC channel data into channel dictionary."""
        # The first 3 bytes are header, so the channel data starts at index 3.
        channel_data = data[3:]
        
        for i in range(16):
            bits = i * 11
            byte_index = bits // 8
            bit_index = bits % 8
            
            # Combine up to 3 bytes in little-endian order
            raw = channel_data[byte_index]
            if byte_index + 1 < len(channel_data):
                raw |= channel_data[byte_index + 1] << 8
            if byte_index + 2 < len(channel_data):
                raw |= channel_data[byte_index + 2] << 16
            
            # Extract 11 bits for this channel
            value = (raw >> bit_index) & 0x07FF
            
            # Convert to µs (approximately 1000-2000); adjust the conversion if needed.
            self.channels[i + 1] = int(value * 0.62 + 881)
    
    def _decode_link_stats(self, data: bytes) -> None:
        """Decode CRSF link statistics data."""
        self.link_stats = LinkStats(
            rssi1=-1 * data[3],
            rssi2=-1 * data[4],
            link_quality=data[5],
            snr=data[6] if data[6] < 128 else data[6] - 256
        )
    
    def _handle_packet(self, packet_type: int, data: bytes) -> None:
        """Process different types of CRSF packets."""
        if packet_type == self.PacketTypes.RC_CHANNELS_PACKED:
            self._decode_channels(data)
        elif packet_type == self.PacketTypes.LINK_STATISTICS:
            self._decode_link_stats(data)
    
    def send_battery_telemetry(self, voltage: float, current: float = 0.0, 
                             mah: int = 0, remaining_percent: int = 0) -> None:
        """
        Send battery telemetry data to the transmitter.
        
        Args:
            voltage: Battery voltage in volts
            current: Current draw in amperes (optional)
            mah: Consumed capacity in mAh (optional)
            remaining_percent: Battery remaining percentage (optional)
        """
        # Convert values to CRSF format
        voltage_scaled = int(voltage * 10)  # 0.1V resolution
        current_scaled = int(current * 10)  # 0.1A resolution
        
        # Create battery sensor payload
        payload = struct.pack('>HHHB',
            voltage_scaled,    # Voltage in 0.1V
            current_scaled,    # Current in 0.1A
            mah,              # Consumed mAh
            remaining_percent  # Remaining percentage
        )
        
        # Frame format: Sync byte, Length, Type, Payload, CRC8
        frame = bytearray([
            self.CRSF_TELEMETRY_SYNC,
            len(payload) + 2,  # +2 for type and CRC
            self.PacketTypes.BATTERY_SENSOR
        ])
        frame.extend(payload)
        
        # Calculate and add CRC
        crc = self._crc8_data(frame[2:])  # CRC of type and payload
        frame.append(crc)
        
        # Send frame
        try:
            self.serial.write(frame)
            self.serial.flush()
        except serial.SerialException as e:
            print(f"Failed to send telemetry: {e}")
    
    def update(self) -> None:
        """
        Update receiver data by reading and processing available packets.
        Call this function regularly to get fresh data.
        """
        if not self.serial or not self.serial.is_open:
            self._connect()
        
        # Read available data
        if self.serial.in_waiting > 0:
            self.input_buffer.extend(self.serial.read(self.serial.in_waiting))
        
        # Process complete packets
        while len(self.input_buffer) > 2:
            if self.input_buffer[0] != self.CRSF_SYNC:
                self.input_buffer.pop(0)
                continue
            
            length = self.input_buffer[1]
            expected_len = length + 2
            
            if expected_len > 64 or expected_len < 4:
                self.input_buffer.pop(0)
                continue
            
            if len(self.input_buffer) >= expected_len:
                packet = self.input_buffer[:expected_len]
                self.input_buffer = self.input_buffer[expected_len:]
                
                if self._validate_frame(packet):
                    self._handle_packet(packet[2], packet)
            else:
                break
    
    def get_channels(self) -> Dict[int, int]:
        """Get latest channel values."""
        return self.channels.copy()
    
    def get_link_stats(self) -> Optional[LinkStats]:
        """Get latest link statistics."""
        return self.link_stats
    
    def close(self):
        """Close the serial connection."""
        if self.serial and self.serial.is_open:
            self.serial.close()
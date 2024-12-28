"""Pre-processes loop packets and possibly make modifications."""

# Standard Python Libraries
import logging

logger = logging.getLogger(__name__)

TX_BATTERY_STATUS_FIELDS = [
    "batteryStatusISS",
    "batteryStatusChannel1",
    "batteryStatusChannel2",
    "batteryStatusChannel3",
    "batteryStatusChannel4",
    "batteryStatusChannel5",
    "batteryStatusChannel6",
    "batteryStatusChannel7",
]


class PacketPreprocessor:
    """Pre-process loop packets."""

    def __init__(self):
        """Initialize the pre-processor."""
        pass

    def process_packet(self, packet: dict) -> dict:
        """Modify the packet before it is processed."""
        logger.debug("Pre-processing packet")
        if "txBatteryStatus" in packet:
            logger.debug("Processing txBatteryStatus")
            txBatteryStatus = packet["txBatteryStatus"]
            # txBatteryStatus is a bitmap.  Break bits into individual fields.
            for i, field in enumerate(TX_BATTERY_STATUS_FIELDS):
                packet[field] = txBatteryStatus & (1 << i)
            del packet["txBatteryStatus"]
        return packet

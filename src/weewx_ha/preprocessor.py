"""Pre-processes loop packets and possibly make modifications."""

# Standard Python Libraries
import logging

logger = logging.getLogger(__name__)

TX_BATTERY_STATUS_FIELDS = [
    "issBatteryStatus",
    "channel1BatteryStatus",
    "channel2BatteryStatus",
    "channel3BatteryStatus",
    "channel4BatteryStatus",
    "channel5BatteryStatus",
    "channel6BatteryStatus",
    "channel7BatteryStatus",
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

"""teltonika-codec8: Parser for Teltonika Codec 8 and Codec 8 Extended AVL packets with DTC decoding."""

__version__ = "0.1.0"

from teltonika_codec8.crc16 import crc16_ibm, verify_crc16
from teltonika_codec8.dtc import decode_dtc_bytes, decode_dtc_int
from teltonika_codec8.models import AvlDataPacket, AvlRecord, GpsElement
from teltonika_codec8.parser import TeltonikaCodecParser

__all__ = [
    "AvlDataPacket",
    "AvlRecord",
    "GpsElement",
    "TeltonikaCodecParser",
    "crc16_ibm",
    "decode_dtc_bytes",
    "decode_dtc_int",
    "verify_crc16",
    "__version__",
]

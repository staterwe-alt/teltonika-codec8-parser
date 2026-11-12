"""SAE J2012 OBD-II Diagnostic Trouble Code (DTC) decoder."""

from __future__ import annotations

import re

_DTC_PREFIXES = ("P", "C", "B", "U")
_ASCII_DTC_RE = re.compile(r"[PCBU][0-9A-F]{4}")


def decode_dtc_int(raw_val: int) -> str:
    """Decode a 16-bit integer according to SAE J2012 standard into a 5-char DTC string (e.g. P0205)."""
    val = raw_val & 0xFFFF
    prefix = _DTC_PREFIXES[(val >> 14) & 0x03]
    d2 = (val >> 12) & 0x03
    d3 = (val >> 8) & 0x0F
    d4 = (val >> 4) & 0x0F
    d5 = val & 0x0F
    return f"{prefix}{d2}{d3:X}{d4:X}{d5:X}"


def decode_dtc_bytes(raw: bytes) -> list[str]:
    """Decode variable-length DTC payload bytes (supports ASCII codes or packed 2-byte integers)."""
    if not raw:
        return []

    # Check if raw bytes represent ASCII DTC string (e.g., b"P0205,P0420")
    try:
        text = raw.decode("ascii", errors="strict").strip("\x00 ")
        ascii_matches = _ASCII_DTC_RE.findall(text.upper())
        if ascii_matches:
            return ascii_matches
    except UnicodeDecodeError:
        pass

    # Otherwise interpret as consecutive 2-byte big-endian SAE J2012 values
    codes: list[str] = []
    for i in range(0, len(raw) - 1, 2):
        val = int.from_bytes(raw[i : i + 2], byteorder="big")
        if val != 0:
            codes.append(decode_dtc_int(val))
    return codes

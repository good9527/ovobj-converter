# -*- coding: utf-8 -*-
"""
pyovobj.core.decompressor
-------------------------
Multi-strategy fault-tolerant decompressor for Ovital (.ovobj) binary files.
Supports legacy, mobile, desktop, VIP, and unpadded Zlib bitstreams.
"""

import zlib

def decompress_ovobj(raw_bytes: bytes) -> bytes:
    """
    Decompresses raw bytes from an .ovobj file across all known Ovital versions.
    
    Strategies:
    1. Standard desktop container (24-byte header, 16-byte CRC/MD5 trailer).
    2. Header-only container (24-byte header, no trailer).
    3. Sliding-window magic detection for Zlib stream headers (0x78 0x9C, 0x78 0x01, 0x78 0xDA, 0x78 0x5E).
    4. Direct unpadded decompression.
    
    :param raw_bytes: Raw binary content read from an .ovobj file.
    :return: Decompressed payload bytes.
    :raises ValueError: If the data cannot be decompressed using any strategy.
    """
    # Strategy 1: Standard Ovital container (skip 24B header, drop 16B trailer)
    if len(raw_bytes) > 40:
        try:
            return zlib.decompress(raw_bytes[24:-16])
        except Exception:
            pass

    # Strategy 2: Only 24-byte header
    if len(raw_bytes) > 24:
        try:
            return zlib.decompress(raw_bytes[24:])
        except Exception:
            pass

    # Strategy 3: Sliding window magic search within first 1024 bytes
    zlib_magics = [b'\x78\x9c', b'\x78\x01', b'\x78\xda', b'\x78\x5e']
    scan_limit = min(len(raw_bytes), 2048)
    for magic in zlib_magics:
        idx = 0
        while True:
            pos = raw_bytes.find(magic, idx, scan_limit)
            if pos == -1:
                break
            try:
                return zlib.decompress(raw_bytes[pos:])
            except Exception:
                pass
            try:
                return zlib.decompress(raw_bytes[pos:-16])
            except Exception:
                pass
            idx = pos + 1

    # Strategy 4: Raw stream without encapsulation
    try:
        return zlib.decompress(raw_bytes)
    except Exception as e:
        raise ValueError(f"Failed to decompress .ovobj file. Unrecognized header format or corrupted data: {e}")

# -*- coding: utf-8 -*-
"""
tests.test_decoder
------------------
Unit tests for coordinate delta bitstream decoding.
"""

import unittest
from pyovobj.core.decoder import decode_coordinate_stream

class TestDecoder(unittest.TestCase):

    def test_zero_delta(self):
        # Tag byte = 0x00 means dy=0, dx=0
        stream = bytes([0x00])
        deltas, consumed = decode_coordinate_stream(stream, 2)
        self.assertEqual(len(deltas), 1)
        self.assertEqual(deltas[0], (0, 0))
        self.assertEqual(consumed, 1)

    def test_k1_positive(self):
        # W = 4 -> K = 1, carry = 0
        # Payload byte 0x24: high nibble = 2, low nibble = 4
        # v1 = (0 << 4) | 2 = 2 -> dy = 2 // 2 = 1
        # v2 = 4 -> dx = 4
        # Tag: sign_y=0, sign_x=0, W=4 -> Tag = 0x04
        stream = bytes([0x04, 0x24])
        deltas, consumed = decode_coordinate_stream(stream, 2)
        self.assertEqual(len(deltas), 1)
        self.assertEqual(deltas[0], (1, 4))
        self.assertEqual(consumed, 2)

    def test_k1_negative_signs(self):
        # Negative signs: Bit 7 = 1 (dy < 0), Bit 6 = 1 (dx < 0)
        # Tag = 0x80 | 0x40 | 0x04 = 0xC4
        stream = bytes([0xC4, 0x24])
        deltas, consumed = decode_coordinate_stream(stream, 2)
        self.assertEqual(len(deltas), 1)
        self.assertEqual(deltas[0], (-1, -4))
        self.assertEqual(consumed, 2)

if __name__ == '__main__':
    unittest.main()

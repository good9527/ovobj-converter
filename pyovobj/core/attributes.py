# -*- coding: utf-8 -*-
"""
pyovobj.core.attributes
-----------------------
Multi-tier attribute extractor supporting standard JSON objects, unbracketed
key-value pairs, and length-prefixed placemark labels across different Ovital versions.
"""

import json
import re

def extract_attributes(blk: bytes, offset: int) -> dict:
    """
    Extracts all attributes located prior to the coordinate header offset.

    Tiers:
    - Tier 1: Search for enclosed JSON structure {...}
    - Tier 2: Search for newline/tab-separated "KEY":"VALUE" pairs without enclosing braces
    - Tier 3: Search for length-prefixed string representing Placemark NAME

    :param blk: Raw binary block containing the feature.
    :param offset: Byte offset where the 24-byte coordinate header begins.
    :return: Dictionary of extracted attributes.
    """
    attrs = {}

    # Tier 1: Look for enclosed JSON structure {...}
    j_end = blk.rfind(b'}', 0, offset)
    if j_end != -1:
        j_start = blk.rfind(b'{', 0, j_end)
        if j_start != -1:
            try:
                raw_json = blk[j_start : j_end + 1].decode('utf-8', errors='replace')
                parsed = json.loads(raw_json)
                if isinstance(parsed, dict):
                    attrs.update(parsed)
            except Exception:
                pass

    # Tier 2: Look for raw key-value pairs "KEY":"VALUE"
    if not attrs:
        kv_matches = re.findall(rb'"([^"\r\n\t]+)":\s*"([^"\r\n\t]*)"', blk[:offset])
        if kv_matches:
            for k_b, v_b in kv_matches:
                k = None
                v = None
                for enc in ('utf-8', 'gbk', 'gb18030'):
                    try:
                        k = k_b.decode(enc)
                        v = v_b.decode(enc)
                        break
                    except Exception:
                        continue
                if k and v is not None:
                    attrs[k] = v

    # Tier 3: Look for length-prefixed Placemark Name (only if no JSON/KV attributes were found)
    if not attrs:
        for p_pos in range(16, max(16, offset - 4)):
            slen = blk[p_pos]
            if 4 <= slen <= 120 and p_pos + 1 + slen <= offset:
                cand = blk[p_pos + 1 : p_pos + 1 + slen]
                if b'\x00' in cand or any(b < 32 and b not in (9, 10, 13) for b in cand):
                    continue
                for enc in ('utf-8', 'gbk', 'gb18030'):
                    try:
                        txt = cand.decode(enc).strip()
                        # Must contain Chinese characters or alphanumeric name, avoid XML/JSON tokens
                        if len(txt) >= 2 and any(ord(c) > 127 for c in txt) and not txt.startswith('{') and '<' not in txt:
                            attrs['NAME'] = txt
                            break
                    except Exception:
                        continue
                if 'NAME' in attrs:
                    break

    return attrs

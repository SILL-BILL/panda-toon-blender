# SPDX-License-Identifier: GPL-3.0-or-later
"""Pure parameter rules; no Blender dependency."""
import math


def ordered_thresholds(low, high):
    if not all(math.isfinite(v) for v in (low, high)):
        raise ValueError("Thresholds must be finite")
    return tuple(sorted((max(0.0, min(1.0, low)), max(0.0, min(1.0, high)))))


def tone_at(value, low, high, dark, mid, light):
    low, high = ordered_thresholds(low, high)
    return dark if value < low else mid if value < high else light

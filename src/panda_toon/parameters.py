# SPDX-License-Identifier: GPL-3.0-or-later
"""Pure parameter rules; no Blender dependency."""
import math


def ordered_thresholds(low, high):
    if not all(math.isfinite(v) for v in (low, high)):
        raise ValueError("Thresholds must be finite")
    return tuple(sorted((max(0.0, min(1.0, low)), max(0.0, min(1.0, high)))))


def tone_at(value, low, high, dark, mid, light, softness=0):
    low, high = ordered_thresholds(low, high)
    if softness == 0:
        return dark if value < low else mid if value < high else light

    def mask(threshold):
        position = max(0.0, min(1.0, (value - threshold) / softness + 0.5))
        return 1.0 - position * position * (3.0 - 2.0 * position)

    return light + (mid - light) * mask(high) + (dark - mid) * mask(low)

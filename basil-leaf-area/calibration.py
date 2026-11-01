"""Area of a planar projection from a calibrated image."""
import math


def area_cm2(pixels, width, height, field_width, field_height,
             distance=None, reference_distance=None):
    for name, value in [('width', width), ('height', height),
                        ('field_width', field_width), ('field_height', field_height)]:
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f'{name} must be finite and positive')
    if not math.isfinite(pixels) or not 0 <= pixels <= width * height:
        raise ValueError('pixels must be within image area')
    if (distance is None) != (reference_distance is None):
        raise ValueError('distance and reference_distance must be supplied together')
    scale = 1.0
    if distance is not None:
        if any(not math.isfinite(v) or v <= 0 for v in (distance, reference_distance)):
            raise ValueError('distances must be finite and positive')
        scale = (distance / reference_distance) ** 2
    return pixels * field_width / width * field_height / height * scale

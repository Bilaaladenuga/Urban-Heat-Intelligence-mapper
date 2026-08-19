"""Cloud masking using Landsat Collection 2 Level-2 QA_PIXEL band.

QA_PIXEL bit layout (USGS C2 L2 documentation)::

    Bit  0 — Fill            (1 = fill / no-data)
    Bit  1 — Dilated Cloud   (1 = dilated cloud)
    Bit  2 — Cirrus          (1 = cirrus cloud)
    Bit  3 — Cloud           (1 = cloud)
    Bit  4 — Cloud Shadow    (1 = cloud shadow)
    Bit  5 — Snow            (1 = snow)
    Bit  6 — Clear           (1 = clear sky — inverted: set = GOOD)
    Bit  7 — Water           (1 = water)
    Bits 8–9   Cloud Shadow Confidence  (00=none, 01=low, 10=med, 11=high)
    Bits 10–11 Cloud Confidence          (00=none, 01=low, 10=med, 11=high)
    Bits 12–13 Snow Confidence            (00=none, 01=low, 10=med, 11=high)
    Bits 14–15 Cirrus Confidence          (00=none, 01=low, 10=med, 11=high)

The mask identifies *bad* pixels (cloud, shadow, cirrus, snow, fill) so
they can be excluded from downstream analysis.  Water is *not* masked here
— it is handled separately in Phase 8 using ESA WorldCover.

**Important:** bit 6 (Clear) is *inverted* — when set, the pixel IS clear.
Do NOT mask on bit 6.

References
----------
USGS (2023).  Landsat Collection 2 Level-2 Science Product Spectral–Spatial
Temporal Characteristics.  QA_PIXEL field description.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

# QA_PIXEL bit positions for cloud / cloud-shadow / cirrus.
# Snow (bit 5) is included as a quality flag but does not affect the urban
# heat analysis — it is documented rather than excluded by default.
# Bit 6 (Clear) is NOT a mask bit — it is inverted (set = good).
BIT_FILL = 0
BIT_DILATED_CLOUD = 1
BIT_CIRRUS = 2
BIT_CLOUD = 3
BIT_CLOUD_SHADOW = 4
BIT_SNOW = 5

# Default bits that produce the *valid* mask (pixels where ALL of these bits
# are 0 are considered valid).  Snow is excluded by default because it is
# extremely rare in Lagos and would add noise to the mask without benefit.
DEFAULT_MASK_BITS = [BIT_FILL, BIT_DILATED_CLOUD, BIT_CIRRUS, BIT_CLOUD, BIT_CLOUD_SHADOW]


def _bit_is_set(value: NDArray[np.uint16], bit: int) -> NDArray[np.bool_]:
    """Return a boolean mask where *bit* is set in *value*."""
    return (value >> bit) & np.uint16(1) == np.uint16(1)


def make_cloud_mask(
    qa_pixel: NDArray[np.uint16],
    *,
    include_snow: bool = False,
) -> NDArray[np.bool_]:
    """Build a boolean valid-pixel mask from QA_PIXEL.

    Parameters
    ----------
    qa_pixel : ndarray of uint16
        The QA_PIXEL band from a Landsat C2 L2 scene.
    include_snow : bool, optional
        If ``True``, snow (bit 5) is also masked.  Default ``False``
        because snow is negligible in Lagos.

    Returns
    -------
    valid_mask : ndarray of bool
        ``True`` where the pixel is **valid** (free of cloud, cloud shadow,
        and cirrus); ``False`` where the pixel is **masked out**.

    Notes
    -----
    - Nodata in QA_PIXEL (value 0 or fill) is treated as invalid.
    - The mask does **not** include water — water masking is a separate
      step in Phase 8 using ESA WorldCover.
    """
    bits = list(DEFAULT_MASK_BITS)
    if include_snow:
        bits.append(BIT_SNOW)

    # Start with "all bits clear" as valid.
    valid = np.ones(qa_pixel.shape, dtype=np.bool_)

    # A pixel is invalid if *any* of the selected bits are set.
    for bit in bits:
        valid &= ~_bit_is_set(qa_pixel, bit)

    # Also mask nodata (value 0 is fill / no-data in C2 L2).
    valid[qa_pixel == 0] = False

    return valid


def apply_cloud_mask(
    bands: dict[str, NDArray[np.uint16]],
    *,
    include_snow: bool = False,
) -> tuple[NDArray[np.bool_], dict[str, NDArray[np.uint16]]]:
    """Mask all analytical bands using QA_PIXEL.

    Parameters
    ----------
    bands : dict
        Mapping ``{band_name: uint16_array}``.  Must contain ``"QA_PIXEL"``.
        Analytical bands are all keys except ``"QA_PIXEL"``.
    include_snow : bool, optional
        Forwarded to :func:`make_cloud_mask`.

    Returns
    -------
    valid_mask : ndarray of bool
        The valid-pixel mask (``True`` = valid).
    masked_bands : dict
        Same keys as *bands* (minus ``"QA_PIXEL"``), but with nodata set to
        ``0`` wherever ``valid_mask`` is ``False``.
    """
    qa = bands["QA_PIXEL"]
    valid_mask = make_cloud_mask(qa, include_snow=include_snow)

    masked: dict[str, NDArray[np.uint16]] = {}
    for name, arr in bands.items():
        if name == "QA_PIXEL":
            continue
        masked_arr = arr.copy()
        masked_arr[~valid_mask] = 0
        masked[name] = masked_arr

    return valid_mask, masked


def valid_pixel_fraction(valid_mask: NDArray[np.bool_]) -> float:
    """Fraction of pixels marked as valid (0.0 – 1.0)."""
    return float(valid_mask.sum() / valid_mask.size)

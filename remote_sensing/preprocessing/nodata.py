"""Nodata handling and validation.

Methodology §3.2 step 4 requires explicit nodata values so that:

- Masked/invalid pixels are never included in statistics.
- No arbitrary fill values (e.g. mean) are applied — pixels are simply
  excluded from analysis.
- Downstream code can rely on a consistent nodata convention across all
  scenes and bands.

The convention for this project:

- Surface-reflectance bands (SR_B4–B7): nodata = 0 (C2 L2 default).
- Surface-temperature band (ST_B10): nodata = 0 (pre-scaled; 0 maps to
  a physically impossible temperature, so no risk of false inclusion).
- QA_PIXEL: nodata = 0 (already handled in cloud_mask module).

References
----------
Methodology §3.2 step 4 — ``Nodata handling: explicit nodata values;
masked/invalid pixels excluded from statistics (never replaced with
arbitrary values)``.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

# Default nodata value for all bands in this project.
NODATA_VALUE = 0

# Physical plausibility ranges for validation.
# Surface reflectance: C2 L2 SR bands are uint16 (0–65535).
# The scaling factor (0.0000275) and offset (-0.2) are applied in Phase 5
# when computing NDVI/NDBI; raw values are stored as-is.  Any uint16 value
# is a valid encoded reflectance; saturated/bright pixels may reach ~65000.
SR_MIN = 0
SR_MAX = 65_535

# Surface temperature: 0–65535 raw uint16, but after scaling:
# LST_K = ST_B10 * 0.00341802 + 149.0  → valid roughly 200–350 K.
# Pre-scaled raw range: ~15 000–60 000 (roughly); anything outside is suspect.
ST_RAW_MIN = 0
ST_RAW_MAX = 65_535

# Bands that are surface-reflectance.
SR_BANDS = {"SR_B4", "SR_B5", "SR_B6", "SR_B7"}
# Band that is surface-temperature.
ST_BAND = "ST_B10"


def set_nodata(
    bands: dict[str, NDArray[np.uint16]],
    valid_mask: NDArray[np.bool_],
) -> dict[str, NDArray[np.uint16]]:
    """Set nodata (0) on all analytical bands where valid_mask is False.

    Parameters
    ----------
    bands : dict
        ``{band_name: uint16_array}`` — analytical bands (not QA_PIXEL).
    valid_mask : ndarray of bool
        ``True`` where the pixel is valid.

    Returns
    -------
    dict
        Same structure with nodata pixels set to 0.
    """
    result: dict[str, NDArray[np.uint16]] = {}
    for name, arr in bands.items():
        out = arr.copy()
        out[~valid_mask] = NODATA_VALUE
        result[name] = out
    return result


def validate_band(
    arr: NDArray[np.uint16],
    band_name: str,
) -> dict:
    """Validate that a band's values are within expected ranges.

    Parameters
    ----------
    arr : ndarray of uint16
        Band array.
    band_name : str
        Name of the band (determines which range to check).

    Returns
    -------
    dict
        ``{min, max, mean, nodata_count, nodata_pct, in_range, band}``
    """
    nodata_count = int((arr == NODATA_VALUE).sum())
    nodata_pct = nodata_count / arr.size * 100

    valid_pixels = arr[arr != NODATA_VALUE]
    if valid_pixels.size == 0:
        return {
            "band": band_name,
            "min": None,
            "max": None,
            "mean": None,
            "nodata_count": nodata_count,
            "nodata_pct": round(nodata_pct, 2),
            "in_range": False,
            "warning": "All pixels are nodata",
        }

    vmin = int(valid_pixels.min())
    vmax = int(valid_pixels.max())
    vmean = float(valid_pixels.mean())

    if band_name in SR_BANDS:
        in_range = vmin >= SR_MIN and vmax <= SR_MAX
    elif band_name == ST_BAND:
        # Raw uint16 — any non-zero value in range [1, 65535] is expected.
        in_range = vmin >= ST_RAW_MIN and vmax <= ST_RAW_MAX
    else:
        # QA_PIXEL or unknown — just check it's uint16 range.
        in_range = vmin >= 0 and vmax <= 65_535

    return {
        "band": band_name,
        "min": vmin,
        "max": vmax,
        "mean": round(vmean, 2),
        "nodata_count": nodata_count,
        "nodata_pct": round(nodata_pct, 2),
        "in_range": in_range,
    }


def validate_all_bands(
    bands: dict[str, NDArray[np.uint16]],
) -> list[dict]:
    """Validate all bands in a scene.

    Parameters
    ----------
    bands : dict
        ``{band_name: uint16_array}``

    Returns
    -------
    list of dict
        One validation record per band.
    """
    return [validate_band(arr, name) for name, arr in bands.items()]


def nodata_summary(valid_mask: NDArray[np.bool_]) -> dict:
    """Summarise the nodata situation for a scene.

    Returns
    -------
    dict
        ``{total_pixels, valid_pixels, nodata_pixels, valid_pct}``
    """
    total = valid_mask.size
    valid = int(valid_mask.sum())
    return {
        "total_pixels": total,
        "valid_pixels": valid,
        "nodata_pixels": total - valid,
        "valid_pct": round(valid / total * 100, 2),
    }

"""Tests for remote_sensing.preprocessing.nodata."""

from __future__ import annotations

import numpy as np

from remote_sensing.preprocessing.nodata import (
    nodata_summary,
    set_nodata,
    validate_all_bands,
    validate_band,
)


class TestSetNodata:
    """Tests for set_nodata()."""

    def test_masks_invalid_pixels(self):
        valid_mask = np.array([[True, False], [False, True]], dtype=np.bool_)
        b4 = np.array([[100, 200], [300, 400]], dtype=np.uint16)
        result = set_nodata({"SR_B4": b4}, valid_mask)
        assert result["SR_B4"][0, 0] == 100
        assert result["SR_B4"][0, 1] == 0
        assert result["SR_B4"][1, 0] == 0
        assert result["SR_B4"][1, 1] == 400

    def test_does_not_modify_original(self):
        valid_mask = np.array([[True, False]], dtype=np.bool_)
        b4 = np.array([[100, 200]], dtype=np.uint16)
        original = b4.copy()
        set_nodata({"SR_B4": b4}, valid_mask)
        np.testing.assert_array_equal(b4, original)

    def test_multiple_bands(self):
        valid_mask = np.array([[True, False]], dtype=np.bool_)
        bands = {
            "SR_B4": np.array([[100, 200]], dtype=np.uint16),
            "SR_B5": np.array([[300, 400]], dtype=np.uint16),
        }
        result = set_nodata(bands, valid_mask)
        assert result["SR_B4"][0, 1] == 0
        assert result["SR_B5"][0, 1] == 0


class TestValidateBand:
    """Tests for validate_band()."""

    def test_sr_in_range(self):
        arr = np.array([[100, 5000], [10000, 0]], dtype=np.uint16)
        result = validate_band(arr, "SR_B4")
        assert result["in_range"] is True
        assert result["min"] == 100
        assert result["max"] == 10000

    def test_sr_out_of_range(self):
        # uint16 max is 65535 — all uint16 values are in range for SR
        # This test verifies that values within uint16 range pass
        arr = np.array([[0, 65535]], dtype=np.uint16)
        result = validate_band(arr, "SR_B4")
        assert result["in_range"] is True

    def test_st_always_valid(self):
        """ST_B10 raw uint16 should always be in range."""
        arr = np.array([[0, 50000], [60000, 0]], dtype=np.uint16)
        result = validate_band(arr, "ST_B10")
        assert result["in_range"] is True

    def test_nodata_count(self):
        arr = np.array([[0, 0, 100], [0, 200, 0]], dtype=np.uint16)
        result = validate_band(arr, "SR_B4")
        assert result["nodata_count"] == 4
        assert abs(result["nodata_pct"] - 66.67) < 0.1

    def test_all_nodata(self):
        arr = np.zeros((10, 10), dtype=np.uint16)
        result = validate_band(arr, "SR_B4")
        assert result["in_range"] is False
        assert "warning" in result


class TestValidateAllBands:
    """Tests for validate_all_bands()."""

    def test_returns_per_band(self):
        bands = {
            "SR_B4": np.array([[100, 200]], dtype=np.uint16),
            "ST_B10": np.array([[45000, 50000]], dtype=np.uint16),
        }
        results = validate_all_bands(bands)
        assert len(results) == 2
        names = {r["band"] for r in results}
        assert names == {"SR_B4", "ST_B10"}


class TestNodataSummary:
    """Tests for nodata_summary()."""

    def test_all_valid(self):
        mask = np.ones((10, 10), dtype=np.bool_)
        result = nodata_summary(mask)
        assert result["valid_pct"] == 100.0
        assert result["nodata_pixels"] == 0

    def test_half_valid(self):
        mask = np.zeros((10, 10), dtype=np.bool_)
        mask[0:5, :] = True
        result = nodata_summary(mask)
        assert result["valid_pct"] == 50.0
        assert result["nodata_pixels"] == 50

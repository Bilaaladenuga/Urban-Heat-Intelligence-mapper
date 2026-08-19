"""Tests for remote_sensing.ndvi.compute."""

from __future__ import annotations

import numpy as np
import pytest

from remote_sensing.ndvi.compute import (
    compute_ndvi,
    compute_stats,
    reflectance,
    validate_ndvi,
)


class TestReflectance:
    """Tests for C2 L2 reflectance scaling."""

    def test_zero_maps_to_negative(self):
        """Raw 0 maps to -0.2 (below valid range)."""
        assert reflectance(np.array([0], dtype=np.uint16))[0] == pytest.approx(-0.2)

    def test_7273_maps_to_zero(self):
        """Raw 7273 (USGS valid minimum) maps to ~0.0."""
        val = reflectance(np.array([7273], dtype=np.uint16))[0]
        assert abs(val) < 0.001

    def test_10000_maps_to_expected(self):
        """Raw 10000 maps to 0.075."""
        val = reflectance(np.array([10000], dtype=np.uint16))[0]
        assert val == pytest.approx(0.075, abs=0.001)

    def test_65535_maps_to_expected(self):
        """Raw 65535 maps to ~1.6."""
        val = reflectance(np.array([65535], dtype=np.uint16))[0]
        assert val == pytest.approx(1.6, abs=0.01)

    def test_preserves_shape(self):
        arr = np.array([[0, 10000], [30000, 65535]], dtype=np.uint16)
        result = reflectance(arr)
        assert result.shape == arr.shape
        assert result.dtype == np.float64


class TestComputeNdvi:
    """Tests for compute_ndvi()."""

    def test_identical_bands_gives_zero(self):
        """When RED == NIR, NDVI should be 0."""
        red = np.array([[10000, 20000]], dtype=np.uint16)
        nir = np.array([[10000, 20000]], dtype=np.uint16)
        ndvi = compute_ndvi(red, nir)
        np.testing.assert_allclose(ndvi, 0.0, atol=1e-6)

    def test_nir_greater_than_red_positive(self):
        """When NIR > RED, NDVI should be positive."""
        red = np.array([[10000]], dtype=np.uint16)
        nir = np.array([[30000]], dtype=np.uint16)
        ndvi = compute_ndvi(red, nir)
        assert ndvi[0, 0] > 0

    def test_red_greater_than_nir_negative(self):
        """When RED > NIR, NDVI should be negative."""
        red = np.array([[30000]], dtype=np.uint16)
        nir = np.array([[10000]], dtype=np.uint16)
        ndvi = compute_ndvi(red, nir)
        assert ndvi[0, 0] < 0

    def test_nodata_excluded(self):
        """Pixels with raw value 0 should be NaN."""
        red = np.array([[0, 10000]], dtype=np.uint16)
        nir = np.array([[0, 30000]], dtype=np.uint16)
        ndvi = compute_ndvi(red, nir)
        assert np.isnan(ndvi[0, 0])
        assert not np.isnan(ndvi[0, 1])

    def test_low_raw_values_excluded(self):
        """Pixels below USGS valid range (< 7273) should be NaN."""
        red = np.array([[5000, 10000]], dtype=np.uint16)
        nir = np.array([[8000, 30000]], dtype=np.uint16)
        ndvi = compute_ndvi(red, nir)
        assert np.isnan(ndvi[0, 0])  # red=5000 < 7273
        assert not np.isnan(ndvi[0, 1])

    def test_output_range(self):
        """NDVI should be in [-1, 1] for valid inputs."""
        np.random.seed(42)
        red = np.random.randint(8000, 40000, (100, 100), dtype=np.uint16)
        nir = np.random.randint(8000, 50000, (100, 100), dtype=np.uint16)
        ndvi = compute_ndvi(red, nir)
        valid = ndvi[~np.isnan(ndvi)]
        assert valid.min() >= -1.0
        assert valid.max() <= 1.0

    def test_output_dtype(self):
        red = np.array([[10000]], dtype=np.uint16)
        nir = np.array([[30000]], dtype=np.uint16)
        ndvi = compute_ndvi(red, nir)
        assert ndvi.dtype == np.float32

    def test_all_nodata(self):
        """All-zero input should produce all NaN."""
        red = np.zeros((10, 10), dtype=np.uint16)
        nir = np.zeros((10, 10), dtype=np.uint16)
        ndvi = compute_ndvi(red, nir)
        assert np.isnan(ndvi).all()


class TestComputeStats:
    """Tests for compute_stats()."""

    def test_basic_stats(self):
        arr = np.array([[-0.5, 0.0, 0.5, 0.8]], dtype=np.float32)
        stats = compute_stats(arr)
        assert stats["min"] == pytest.approx(-0.5, abs=0.001)
        assert stats["max"] == pytest.approx(0.8, abs=0.001)
        assert stats["mean"] == pytest.approx(0.2, abs=0.01)
        assert stats["valid_pixels"] == 4

    def test_with_nan(self):
        arr = np.array([[np.nan, 0.5, np.nan, 0.3]], dtype=np.float32)
        stats = compute_stats(arr)
        assert stats["valid_pixels"] == 2
        assert stats["nan_count"] == 2
        assert stats["valid_pct"] == pytest.approx(50.0, abs=0.1)

    def test_all_nan(self):
        arr = np.full((5, 5), np.nan, dtype=np.float32)
        stats = compute_stats(arr)
        assert stats["valid_pixels"] == 0
        assert stats["mean"] is None


class TestValidateNdvi:
    """Tests for validate_ndvi()."""

    def test_all_valid(self):
        arr = np.array([[-0.5, 0.0, 0.5, 0.8]], dtype=np.float32)
        result = validate_ndvi(arr)
        assert result["range_ok"] is True
        assert result["out_of_range_count"] == 0

    def test_out_of_range(self):
        arr = np.array([[-0.5, 1.5, 0.3]], dtype=np.float32)
        result = validate_ndvi(arr)
        assert result["range_ok"] is False
        assert result["out_of_range_count"] == 1

    def test_land_cover_expectations(self):
        """Mix of water, vegetation, and bare pixels."""
        arr = np.array([[-0.3, 0.1, 0.6, 0.8, -0.1]], dtype=np.float32)
        result = validate_ndvi(arr)
        assert result["water_pct"] > 0  # negative NDVI
        assert result["veg_pct"] > 0   # 0.4-0.9 range
        assert result["bare_urban_pct"] > 0  # <= 0.2

    def test_all_nan(self):
        arr = np.full((5, 5), np.nan, dtype=np.float32)
        result = validate_ndvi(arr)
        assert result["range_ok"] is False

"""Tests for remote_sensing.preprocessing.align."""

from __future__ import annotations

import pathlib

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_bounds

from remote_sensing.preprocessing.align import (
    check_alignment,
    verify_reference_grid,
)


@pytest.fixture
def make_raster(tmp_path: pathlib.Path):
    """Factory fixture: create a raster with given CRS/resolution/bounds."""
    _id = [0]

    def _make(
        crs: str = "EPSG:32631",
        res: float = 30.0,
        bounds: tuple[float, float, float, float] = (467000, 704000, 649000, 740000),
        bands: int = 1,
    ) -> pathlib.Path:
        _id[0] += 1
        path = tmp_path / f"raster_{_id[0]}.tif"
        w = max(1, int((bounds[2] - bounds[0]) / res))
        h = max(1, int((bounds[3] - bounds[1]) / res))
        transform = from_bounds(*bounds, w, h)
        meta = {
            "driver": "GTiff",
            "width": w,
            "height": h,
            "count": bands,
            "dtype": "uint16",
            "crs": crs,
            "transform": transform,
        }
        with rasterio.open(path, "w", **meta) as dst:
            for i in range(1, bands + 1):
                dst.write(np.ones((h, w), dtype=np.uint16) * i, i)
        return path

    return _make


class TestCheckAlignment:
    """Tests for check_alignment()."""

    def test_identical_rasters_aligned(self, make_raster):
        """Two identical rasters should be aligned."""
        a = make_raster()
        b = make_raster()  # same params
        result = check_alignment([a, b])
        assert result["aligned"] is True

    def test_different_crs_not_aligned(self, make_raster):
        """Different CRS → not aligned."""
        a = make_raster(crs="EPSG:32631")
        b = make_raster(crs="EPSG:4326", res=0.002, bounds=(3.0, 6.0, 4.0, 7.0))
        result = check_alignment([a, b])
        assert result["aligned"] is False

    def test_different_resolution_not_aligned(self, make_raster):
        """Different resolution → not aligned."""
        a = make_raster(res=30.0)
        b = make_raster(res=60.0)
        result = check_alignment([a, b])
        assert result["aligned"] is False

    def test_different_bounds_not_aligned(self, make_raster):
        """Different bounds → not aligned."""
        a = make_raster(bounds=(467000, 704000, 649000, 740000))
        b = make_raster(bounds=(468000, 705000, 650000, 741000))
        result = check_alignment([a, b])
        assert result["aligned"] is False

    def test_details_returned(self, make_raster):
        a = make_raster()
        result = check_alignment([a])
        assert len(result["details"]) == 1
        assert "crs" in result["details"][0]


class TestVerifyReferenceGrid:
    """Tests for verify_reference_grid()."""

    def test_matching_grid(self, make_raster):
        """UTM 31N, 30m → matches reference."""
        path = make_raster(crs="EPSG:32631", res=30.0)
        result = verify_reference_grid(path)
        assert result["matches"] is True
        assert result["crs_ok"] is True
        assert result["scale_ok"] is True

    def test_wrong_crs(self, make_raster):
        """WGS84 with degree-scale bounds → does not match."""
        path = make_raster(crs="EPSG:4326", res=0.002, bounds=(3.0, 6.0, 4.0, 7.0))
        result = verify_reference_grid(path)
        assert result["matches"] is False
        assert result["crs_ok"] is False

    def test_wrong_resolution(self, make_raster):
        """60m → does not match."""
        path = make_raster(res=60.0)
        result = verify_reference_grid(path)
        assert result["matches"] is False
        assert result["scale_ok"] is False

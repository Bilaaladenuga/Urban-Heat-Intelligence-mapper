"""Tests for remote_sensing.preprocessing.clip."""

from __future__ import annotations

import json
import pathlib

import geopandas as gpd
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_bounds

from remote_sensing.preprocessing.clip import clip_info, clip_raster, load_boundary


@pytest.fixture
def sample_raster(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a small test raster (100x100, UTM 31N, 6 bands)."""
    path = tmp_path / "test.tif"
    transform = from_bounds(467000, 704000, 649000, 740000, 100, 100)
    meta = {
        "driver": "GTiff",
        "width": 100,
        "height": 100,
        "count": 6,
        "dtype": "uint16",
        "crs": "EPSG:32631",
        "transform": transform,
        "nodata": 0,
    }
    with rasterio.open(path, "w", **meta) as dst:
        for i in range(1, 7):
            arr = np.random.randint(100, 5000, (100, 100), dtype=np.uint16)
            dst.write(arr, i)
    return path


@pytest.fixture
def boundary_geojson(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a small GeoJSON polygon that clips the test raster (in UTM 31N)."""
    path = tmp_path / "boundary.geojson"
    # A rectangle covering the middle 50% of the raster (in UTM 31N coordinates)
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [480000, 710000],
                            [520000, 710000],
                            [520000, 730000],
                            [480000, 730000],
                            [480000, 710000],
                        ]
                    ],
                },
                "properties": {},
            }
        ],
    }
    with open(path, "w") as f:
        json.dump(geojson, f)
    # Write with explicit CRS in the GeoJSON
    gdf = gpd.GeoDataFrame.from_features(
        [geojson["features"][0]], crs="EPSG:32631"
    )
    gdf.to_file(path, driver="GeoJSON")
    return path


@pytest.fixture
def boundary_wgs84(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a small GeoJSON polygon in WGS84 for reprojection tests."""
    path = tmp_path / "boundary_wgs84.geojson"
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [3.4, 6.4],
                            [3.8, 6.4],
                            [3.8, 6.6],
                            [3.4, 6.6],
                            [3.4, 6.4],
                        ]
                    ],
                },
                "properties": {},
            }
        ],
    }
    with open(path, "w") as f:
        json.dump(geojson, f)
    return path


class TestLoadBoundary:
    """Tests for load_boundary()."""

    def test_loads_geojson(self, boundary_geojson: pathlib.Path):
        geoms = load_boundary(boundary_geojson, target_crs="EPSG:32631")
        assert len(geoms) == 1
        assert geoms[0]["type"] == "Polygon"

    def test_reprojects_wgs84_to_utm(self, boundary_wgs84: pathlib.Path):
        """WGS84 input should be reprojected to UTM 31N."""
        geoms = load_boundary(boundary_wgs84, target_crs="EPSG:32631")
        coords = geoms[0]["coordinates"][0]
        # UTM 31N coordinates should be in hundreds of thousands
        assert all(400000 < c[0] < 700000 for c in coords)
        assert all(600000 < c[1] < 800000 for c in coords)

    def test_utm_input_passes_through(self, boundary_geojson: pathlib.Path):
        """Already-UTM input should pass through unchanged."""
        geoms = load_boundary(boundary_geojson, target_crs="EPSG:32631")
        coords = geoms[0]["coordinates"][0]
        # Should be in UTM range
        assert all(400000 < c[0] < 700000 for c in coords)


class TestClipRaster:
    """Tests for clip_raster()."""

    def test_clip_reduces_pixels(
        self, sample_raster: pathlib.Path, boundary_geojson: pathlib.Path, tmp_path: pathlib.Path
    ):
        """Clipping to a smaller boundary should mask some pixels."""
        geoms = load_boundary(boundary_geojson, target_crs="EPSG:32631")
        dst_path = tmp_path / "clipped.tif"
        meta = clip_raster(sample_raster, geoms, dst_path, nodata=0)

        assert dst_path.exists()
        # Clipping to a smaller polygon reduces the raster size
        assert meta["dst_shape"][1] < meta["src_shape"][1]  # height reduced
        assert meta["dst_shape"][2] < meta["src_shape"][2]  # width reduced
        # Some pixels outside the polygon should be nodata
        with rasterio.open(dst_path) as src:
            arr = src.read(1)
            assert (arr == 0).any()

    def test_nodata_outside_boundary(
        self, sample_raster: pathlib.Path, boundary_geojson: pathlib.Path, tmp_path: pathlib.Path
    ):
        """Pixels outside the boundary should be nodata."""
        geoms = load_boundary(boundary_geojson, target_crs="EPSG:32631")
        dst_path = tmp_path / "clipped.tif"
        clip_raster(sample_raster, geoms, dst_path, nodata=0)

        with rasterio.open(dst_path) as src:
            arr = src.read(1)
            # Some pixels should be nodata (0)
            assert (arr == 0).any()

    def test_output_has_nodata_set(
        self, sample_raster: pathlib.Path, boundary_geojson: pathlib.Path, tmp_path: pathlib.Path
    ):
        geoms = load_boundary(boundary_geojson, target_crs="EPSG:32631")
        dst_path = tmp_path / "clipped.tif"
        clip_raster(sample_raster, geoms, dst_path, nodata=0)

        with rasterio.open(dst_path) as src:
            assert src.nodata == 0


class TestClipInfo:
    """Tests for clip_info()."""

    def test_returns_dict(self, sample_raster: pathlib.Path):
        info = clip_info(sample_raster)
        assert "bands" in info
        assert "crs" in info
        assert info["bands"] == 6
        assert info["crs"] == "EPSG:32631"

"""Tests for remote_sensing.preprocessing.cloud_mask."""

from __future__ import annotations

import numpy as np

from remote_sensing.preprocessing.cloud_mask import (
    apply_cloud_mask,
    make_cloud_mask,
    valid_pixel_fraction,
)


class TestMakeCloudMask:
    """Tests for make_cloud_mask()."""

    def test_fill_is_masked(self):
        """QA_PIXEL = 0 is fill/nodata and should be masked."""
        qa = np.array([[0, 0], [0, 0]], dtype=np.uint16)
        mask = make_cloud_mask(qa)
        assert mask.sum() == 0

    def test_clean_pixel_is_valid(self):
        """A pixel with only the Clear bit (6) set should be valid."""
        qa = np.array([[64, 64], [64, 64]], dtype=np.uint16)  # bit 6 only
        mask = make_cloud_mask(qa)
        assert mask.all()

    def test_cloud_bit_masks_pixel(self):
        """Bit 3 (Cloud) set should mask the pixel."""
        # pixel (0,0) = 8 (bit 3 only = cloud), pixel (0,1) = 64 (bit 6 = clear)
        qa = np.array([[8, 64], [64, 64]], dtype=np.uint16)
        mask = make_cloud_mask(qa)
        assert mask[0, 0] is np.False_  # cloud → masked
        assert mask[0, 1] is np.True_   # clear → valid

    def test_cloud_shadow_masks_pixel(self):
        """Bit 4 (Cloud Shadow) set should mask the pixel."""
        # pixel (0,0) = 16 (bit 4 = cloud shadow)
        qa = np.array([[16, 64], [64, 64]], dtype=np.uint16)
        mask = make_cloud_mask(qa)
        assert mask[0, 0] is np.False_  # cloud shadow → masked

    def test_cirrus_masks_pixel(self):
        """Bit 2 (Cirrus) set should mask the pixel."""
        # pixel (0,0) = 4 (bit 2 = cirrus)
        qa = np.array([[4, 64], [64, 64]], dtype=np.uint16)
        mask = make_cloud_mask(qa)
        assert mask[0, 0] is np.False_  # cirrus → masked

    def test_dilated_cloud_masks_pixel(self):
        """Bit 1 (Dilated Cloud) set should mask the pixel."""
        # pixel (0,0) = 2 (bit 1 = dilated cloud)
        qa = np.array([[2, 64], [64, 64]], dtype=np.uint16)
        mask = make_cloud_mask(qa)
        assert mask[0, 0] is np.False_  # dilated cloud → masked

    def test_snow_not_masked_by_default(self):
        """Bit 5 (Snow) should NOT mask by default."""
        # pixel (0,0) = 32 (bit 5 only = snow)
        qa = np.array([[32, 64], [64, 64]], dtype=np.uint16)
        mask = make_cloud_mask(qa)
        assert mask[0, 0] is np.True_  # snow → NOT masked by default

    def test_snow_masked_when_enabled(self):
        """Bit 5 (Snow) should mask when include_snow=True."""
        qa = np.array([[32, 64], [64, 64]], dtype=np.uint16)
        mask = make_cloud_mask(qa, include_snow=True)
        assert mask[0, 0] is np.False_  # snow → masked when enabled

    def test_multiple_bits_set(self):
        """Multiple bad bits set should still mask the pixel."""
        # bits 1, 3, 4 = 2 + 8 + 16 = 26
        # pixel (0,0) = 0 (fill), pixel (0,1) = 26 (cloud flags)
        # pixel (1,0) = 64 (clear), pixel (1,1) = 0 (fill)
        qa = np.array([[0, 26], [64, 0]], dtype=np.uint16)
        mask = make_cloud_mask(qa)
        assert mask[0, 0] is np.False_  # fill → masked
        assert mask[0, 1] is np.False_  # bits 1,3,4 set → masked
        assert mask[1, 0] is np.True_   # bit 6 only → clear → valid
        assert mask[1, 1] is np.False_  # fill → masked

    def test_realistic_lc09_values(self):
        """Realistic LC09 QA_PIXEL values from the Lagos scene."""
        # 21762 = bits 1,8,10,12,14 (dilated cloud + confidence bits) → bit 1 → masked
        # 21824 = bits 6,8,10,12,14 (clear + confidence bits) → no cloud flags → valid
        # 64 = bit 6 only (clear) → valid
        # 0 = fill → masked
        qa = np.array([[0, 21762], [21824, 64]], dtype=np.uint16)
        mask = make_cloud_mask(qa)
        assert mask[0, 0] is np.False_  # fill → masked
        assert mask[0, 1] is np.False_  # 21762: bit 1 set → masked
        assert mask[1, 0] is np.True_   # 21824: only bits 6,8,10,12,14 → valid
        assert mask[1, 1] is np.True_   # 64: bit 6 only → valid

    def test_confidence_bits_not_masked(self):
        """Bits 8-15 (confidence) should not cause masking."""
        # bit 8 only = 256 → should be valid (confidence bit, not cloud flag)
        qa = np.array([[256, 512], [1024, 2048]], dtype=np.uint16)
        mask = make_cloud_mask(qa)
        assert mask.all()  # all should be valid

    def test_shape_preserved(self):
        """Output shape matches input shape."""
        qa = np.zeros((100, 200), dtype=np.uint16)
        mask = make_cloud_mask(qa)
        assert mask.shape == (100, 200)
        assert mask.dtype == np.bool_


class TestApplyCloudMask:
    """Tests for apply_cloud_mask()."""

    def test_masks_all_bands(self):
        """All analytical bands should be masked where QA_PIXEL indicates."""
        # pixel (0,1) = 8 (cloud) → masked
        qa = np.array([[64, 8], [0, 64]], dtype=np.uint16)
        b4 = np.array([[100, 200], [300, 400]], dtype=np.uint16)
        b5 = np.array([[50, 60], [70, 80]], dtype=np.uint16)

        _valid_mask, masked = apply_cloud_mask(
            {"SR_B4": b4, "SR_B5": b5, "QA_PIXEL": qa}
        )

        assert "QA_PIXEL" not in masked
        assert masked["SR_B4"].shape == b4.shape
        # Pixel (0,1) should be masked (cloud)
        assert masked["SR_B4"][0, 1] == 0
        assert masked["SR_B5"][0, 1] == 0
        # Pixel (0,0) should be preserved (clear)
        assert masked["SR_B4"][0, 0] == 100


class TestValidPixelFraction:
    """Tests for valid_pixel_fraction()."""

    def test_all_valid(self):
        mask = np.ones((10, 10), dtype=np.bool_)
        assert valid_pixel_fraction(mask) == 1.0

    def test_all_invalid(self):
        mask = np.zeros((10, 10), dtype=np.bool_)
        assert valid_pixel_fraction(mask) == 0.0

    def test_half_valid(self):
        mask = np.zeros((10, 10), dtype=np.bool_)
        mask[0:5, :] = True
        assert abs(valid_pixel_fraction(mask) - 0.5) < 0.001

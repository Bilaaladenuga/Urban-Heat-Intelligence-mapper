"""Shared fixtures for remote_sensing tests.

``FakeEE`` mimics the tiny slice of the Earth Engine API the acquisition
modules use, so query construction and selection logic are testable
without credentials or network. ``getInfo`` results are consumed in
order from a queue supplied by each test.
"""

from __future__ import annotations

import pytest


class FakeFilter:
    def __init__(self, op: str | None = None, *args):
        self.op = op
        self.args = args

    @staticmethod
    def eq(a, b) -> FakeFilter:
        return FakeFilter("eq", a, b)

    @staticmethod
    def lte(a, b) -> FakeFilter:
        return FakeFilter("lte", a, b)


class FakeTask:
    _counter = 0

    def __init__(self, kwargs: dict):
        FakeTask._counter += 1
        self.kwargs = kwargs
        self.id = f"task_{FakeTask._counter}"
        self.started = False

    def start(self) -> None:
        self.started = True


class FakeCollection:
    def __init__(self, ee, cid):
        self._ee = ee
        self.cid = cid
        self.filters: list[tuple] = []

    def filterBounds(self, geometry):
        self.filters.append(("filterBounds", geometry))
        return self

    def filterDate(self, start, end):
        self.filters.append(("filterDate", start, end))
        return self

    def filter(self, filt):
        self.filters.append(("filter", filt))
        return self

    def merge(self, other):
        return self

    def getInfo(self) -> dict:
        return next(self._ee._results)


class FakeList:
    def __init__(self, items):
        self._items = list(items)

    def map(self, fn):
        return FakeList(fn(c) for c in self._items)

    def __iter__(self):
        return iter(self._items)


class FakeImage:
    def __init__(self, image_id):
        self.image_id = image_id
        self.selected: list | None = None

    def select(self, bands):
        self.selected = list(bands)
        return self


class FakeEE:
    Filter = FakeFilter

    class batch:
        class Export:
            class image:
                @staticmethod
                def toDrive(**kwargs):
                    return FakeTask(kwargs)

    def Image(self, image_id):
        return FakeImage(image_id)

    def __init__(self, getinfo_results: list[dict] | None = None):
        self._results = iter(getinfo_results or [{"features": []}])
        self._collections: dict[str, FakeCollection] = {}

    def List(self, items):
        return FakeList(items)

    def ImageCollection(self, cid):
        key = str(cid)
        if key not in self._collections:
            self._collections[key] = FakeCollection(self, cid)
        return self._collections[key]

    def collections_seen(self) -> list[str]:
        return [c.cid for c in self._collections.values()]

    def Geometry(self, geojson):
        return ("geometry", geojson)


@pytest.fixture
def sample_feature() -> dict:
    return {
        "type": "Feature",
        "id": "LC08_191055_20230115",
        "properties": {
            "system:index": "LC08_191055_20230115",
            "SPACECRAFT_ID": "LANDSAT_8",
            "DATE_ACQUIRED": "2023-01-15",
            "CLOUD_COVER": 12.5,
            "WRS_PATH": 191,
            "WRS_ROW": 55,
            "COLLECTION_ID": "LANDSAT/LC08/C02/T1_L2",
            "LANDSAT_PRODUCT_ID": "LC08_L2SP_191055_20230115_02_T1",
        },
    }

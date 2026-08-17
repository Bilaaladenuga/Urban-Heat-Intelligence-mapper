"""Scene record model (Phase 3 — acquisition metadata).

A :class:`SceneRecord` captures everything needed to reproduce a scene's
selection and processing later: identity (scene id, date, sensor),
selection context (seasonal window, selection rule, cloud cover) and the
processing parameters that were exported with it. Records are persisted
as JSON alongside the imagery (``data/processed/imagery/``, gitignored).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field


@dataclass
class SceneRecord:
    """One acquired Landsat scene and its selection/export metadata."""

    scene_id: str            # e.g. LC08_191055_20230115
    satellite: str           # e.g. LANDSAT_8
    date: str                # ISO date (YYYY-MM-DD)
    wrs_path: int
    wrs_row: int
    cloud_cover_pct: float
    window: str              # 'dry' | 'wet'
    selection: str           # 'best_in_window' | 'fallback_above_threshold'
    source_collection: str   # GEE collection id
    bands: list[str]
    crs: str
    scale_meters: int
    geometry_source: str = ""      # path to the AOI GeoJSON used
    cloud_above_threshold: bool = False
    notes: str = ""                # selection rationale / deviations
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> SceneRecord:
        return cls(**data)


def dumps(record: SceneRecord) -> str:
    """JSON-serialize a record (stable key order via dataclass fields)."""
    return json.dumps(record.to_dict(), indent=2, sort_keys=False)

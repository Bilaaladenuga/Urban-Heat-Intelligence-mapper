"""Catalog search and scene selection (Phase 3 — acquisition).

Search the Landsat 8/9 C2 L2 collections on Google Earth Engine for a
seasonal window and the study-area geometry, then select the best scene
per window (lowest cloud cover within the threshold, with a documented
fallback to the lowest-cloud scene when nothing qualifies).

The GEE interaction is isolated in :func:`fetch_features` so the pure
selection logic is unit-testable without credentials.
"""

from __future__ import annotations

import logging

from . import config
from .models import SceneRecord

logger = logging.getLogger(__name__)


def window_date_range(window: str, year: int) -> tuple[str, str]:
    """Return inclusive (start, end) ISO dates for a seasonal window.

    Dry (Nov-Mar): start = ``{year-1}-11-01``, end = ``{year}-03-31``.
    Wet (Apr-Oct): start = ``{year}-04-01``, end = ``{year}-10-31``.
    """
    start_month, end_month = config.SEASONAL_WINDOWS[window]
    if start_month > end_month:  # year-crossing window (dry)
        start = f"{year - 1}-{start_month:02d}-01"
        end = f"{year}-{end_month:02d}-31"
    else:
        start = f"{year}-{start_month:02d}-01"
        end = f"{year}-{end_month:02d}-31"
    return start, end


def build_search_query(
    ee,
    *,
    geometry,
    window: str,
    year: int,
    max_cloud_pct: float | None,
) -> object:
    """Build the GEE ImageCollection query for one seasonal window.

    Filters: path/row (WRS 191/055), date range for the window, the
    study-area geometry, and (optionally) a cloud-cover ceiling.

    ``max_cloud_pct=None`` returns the unfiltered window (used for the
    fallback search when no scene meets the threshold).
    """
    start, end = window_date_range(window, year)
    collections = ee.List(config.COLLECTIONS).map(
        lambda cid: _single_collection(ee, cid, geometry, start, end, max_cloud_pct)
    )
    return ee.ImageCollection(collections).flatten()


def _single_collection(ee, cid, geometry, start, end, max_cloud_pct):
    """Build one collection's chain with the shared filters applied."""
    collection = (
        ee.ImageCollection(cid)
        .filterBounds(geometry)
        .filterDate(start, end)
        .filter(ee.Filter.eq("WRS_PATH", config.WRS_PATH))
        .filter(ee.Filter.eq("WRS_ROW", config.WRS_ROW))
    )
    if max_cloud_pct is not None:
        collection = collection.filter(ee.Filter.lte("CLOUD_COVER", max_cloud_pct))
    return collection


def fetch_features(ee, query) -> list[dict]:
    """Run a query and return the scene features (``getInfo`` payload)."""
    info = query.getInfo()
    return list(info.get("features", []))


def records_from_features(features: list[dict], *, window: str) -> list[SceneRecord]:
    """Convert raw GEE feature dicts into :class:`SceneRecord` lists.

    Pure function: no GEE calls, so it is unit-tested with fixtures.
    """
    records: list[SceneRecord] = []
    for feature in features:
        props = feature.get("properties", {})
        scene_id = props.get("system:index") or feature.get("id", "")
        if not scene_id:
            continue
        satellite = props.get("SPACECRAFT_ID", "")
        date = props.get("DATE_ACQUIRED", "")
        if not date:
            date = (props.get("system:time_start") or "").split("T")[0]
        records.append(
            SceneRecord(
                scene_id=scene_id,
                satellite=satellite,
                date=date,
                wrs_path=int(props.get("WRS_PATH", config.WRS_PATH)),
                wrs_row=int(props.get("WRS_ROW", config.WRS_ROW)),
                cloud_cover_pct=float(props.get("CLOUD_COVER", -1.0)),
                window=window,
                selection="",
                source_collection=props.get("COLLECTION_ID", ""),
                bands=list(config.BANDS),
                crs=config.EXPORT_CRS,
                scale_meters=config.SCALE_METERS,
                extra={"landsat_product_id": props.get("LANDSAT_PRODUCT_ID", "")},
            )
        )
    return records


def select_best(records: list[SceneRecord]) -> SceneRecord | None:
    """Return the lowest-cloud record, or None for an empty list."""
    if not records:
        return None
    return min(records, key=lambda r: r.cloud_cover_pct)


def plan_window(
    ee,
    *,
    geometry,
    window: str,
    year: int,
    cloud_threshold_pct: float,
) -> tuple[SceneRecord | None, list[str]]:
    """Select the best scene for one window, with documented fallback.

    Returns ``(record, messages)`` where ``messages`` records the
    selection rationale (or why no scene was available). Cloud-ceiling
    deviations are recorded on the record itself (methodology 3.1).
    """
    messages: list[str] = []

    within = fetch_features(
        ee,
        build_search_query(
            ee, geometry=geometry, window=window, year=year,
            max_cloud_pct=cloud_threshold_pct,
        ),
    )
    candidates = records_from_features(within, window=window)
    best = select_best(candidates)
    if best is not None:
        best.selection = "best_in_window"
        best.cloud_above_threshold = False
        messages.append(
            f"{window}: selected {best.scene_id} "
            f"(cloud {best.cloud_cover_pct:.1f}% <= {cloud_threshold_pct}%)"
        )
        return best, messages

    # Fallback: nothing under the ceiling — take the lowest-cloud scene in
    # the window and record the deviation (never force a cloudy scene).
    all_features = fetch_features(
        ee,
        build_search_query(
            ee, geometry=geometry, window=window, year=year, max_cloud_pct=None,
        ),
    )
    all_records = records_from_features(all_features, window=window)
    fallback = select_best(all_records)
    if fallback is None:
        messages.append(f"{window}: no scenes available in the window")
        return None, messages

    fallback.selection = "fallback_above_threshold"
    fallback.cloud_above_threshold = fallback.cloud_cover_pct > cloud_threshold_pct
    fallback.notes = (
        f"No scene with cloud <= {cloud_threshold_pct}% in {window} window; "
        f"used lowest-cloud scene ({fallback.cloud_cover_pct:.1f}%)."
    )
    messages.append(fallback.notes)
    return fallback, messages

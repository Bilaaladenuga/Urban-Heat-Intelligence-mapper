"""Metadata persistence (Phase 3 — acquisition).

Every selected scene gets a JSON record (``{scene_id}.json``) and the
run manifest (``manifest.json``) is updated with the full record list.
Records live under ``data/processed/imagery/`` (gitignored) so the
selection rationale survives across runs without bloating Git.
"""

from __future__ import annotations

import json
import pathlib

from . import config
from .models import SceneRecord, dumps


def save_record(record: SceneRecord, directory: pathlib.Path | None = None) -> pathlib.Path:
    """Write one scene record as JSON; returns the written path."""
    directory = directory or config.IMAGERY_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{record.scene_id}.json"
    path.write_text(dumps(record), encoding="utf-8")
    return path


def load_record(path: pathlib.Path) -> SceneRecord:
    """Read a scene record JSON file back into a :class:`SceneRecord`."""
    return SceneRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))


def update_manifest(
    records: list[SceneRecord],
    manifest_file: pathlib.Path | None = None,
) -> pathlib.Path:
    """Replace the manifest with the given records; returns the path."""
    manifest_file = manifest_file or config.MANIFEST_FILE
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": config.COLLECTIONS,
        "wrs_path_row": [config.WRS_PATH, config.WRS_ROW],
        "bands": config.BANDS,
        "records": [r.to_dict() for r in records],
    }
    manifest_file.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return manifest_file


def load_manifest(manifest_file: pathlib.Path | None = None) -> list[SceneRecord]:
    """Read the manifest back into a list of records (empty if absent)."""
    manifest_file = manifest_file or config.MANIFEST_FILE
    if not manifest_file.exists():
        return []
    payload = json.loads(manifest_file.read_text(encoding="utf-8"))
    return [SceneRecord.from_dict(r) for r in payload.get("records", [])]

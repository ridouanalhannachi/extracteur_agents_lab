"""Stable, local draft state for the Streamlit timetable editor."""
from __future__ import annotations

import hashlib

import pandas as pd


DRAFT_KEY = "_edt_details_draft"
APPLIED_KEY = "_edt_details_applied"
SOURCE_KEY = "_edt_details_source"
FLASH_KEY = "_edt_details_flash"
EDITOR_KEY = "details_editor"


def upload_fingerprint(files) -> str:
    digest = hashlib.sha256()
    for uploaded in files:
        digest.update(str(uploaded.name).encode("utf-8"))
        digest.update(b"\0")
        digest.update(uploaded.getvalue())
        digest.update(b"\0")
    return digest.hexdigest()


def frame_fingerprint(frame: pd.DataFrame) -> str:
    """Include row order, columns and export-visible values in the comparison."""
    payload = frame.fillna("").to_json(
        orient="split", force_ascii=False, date_format="iso", double_precision=12
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def prepare_editor(baseline: pd.DataFrame, source: str, state):
    """Return the seed and notices before the widget is instantiated."""
    previous_source = state.get(SOURCE_KEY)
    source_changed = previous_source is not None and previous_source != source
    if previous_source != source:
        state[DRAFT_KEY] = baseline.copy()
        state[APPLIED_KEY] = baseline.copy()
        state.pop(EDITOR_KEY, None)
        state[SOURCE_KEY] = source
    if not isinstance(state.get(APPLIED_KEY), pd.DataFrame):
        state[APPLIED_KEY] = baseline.copy()
    if not isinstance(state.get(DRAFT_KEY), pd.DataFrame):
        state[DRAFT_KEY] = state[APPLIED_KEY].copy()

    # While mounted, Streamlit reapplies the widget delta to the original input.
    # After navigation the widget key is absent, so seed it from our durable draft.
    draft = state.get(DRAFT_KEY)
    if EDITOR_KEY not in state and isinstance(draft, pd.DataFrame):
        return draft.copy(), source_changed
    return baseline.copy(), source_changed


def remember_editor_result(edited: pd.DataFrame, state) -> None:
    state[DRAFT_KEY] = edited.copy()


def apply_editor_result(state, edited: pd.DataFrame) -> None:
    """Callback: runs before the next script pass, so clearing the widget is safe."""
    state[DRAFT_KEY] = edited.copy()
    state[APPLIED_KEY] = edited.copy()
    state.pop(EDITOR_KEY, None)
    state[FLASH_KEY] = "applied"


def cancel_editor_changes(state) -> None:
    """Restore the last explicit checkpoint without changing SQLite or Drive."""
    applied = state.get(APPLIED_KEY)
    if isinstance(applied, pd.DataFrame):
        state[DRAFT_KEY] = applied.copy()
    state.pop(EDITOR_KEY, None)
    state[FLASH_KEY] = "cancelled"

"""Pytest configuration helpers for the Collect project."""

from __future__ import annotations

import pathlib


_ORIGINAL_IS_DIR = pathlib.Path.is_dir


def _safe_is_dir(path_obj: pathlib.Path) -> bool:
    try:
        return _ORIGINAL_IS_DIR(path_obj)
    except OSError as error:
        if getattr(error, "winerror", None) == 1920:
            return False
        raise


pathlib.Path.is_dir = _safe_is_dir  # type: ignore[assignment]


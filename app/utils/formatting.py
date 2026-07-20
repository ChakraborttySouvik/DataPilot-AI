"""Small display-formatting helpers used by the UI layer."""

from __future__ import annotations


def format_bytes(size_bytes: int) -> str:
    """Convert a byte count into a human-readable string.

    Args:
        size_bytes: Number of bytes.

    Returns:
        A human-readable string, e.g. "512 B", "3.4 KB", "1.2 MB".
    """
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024.0:
            return f"{size:.2f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

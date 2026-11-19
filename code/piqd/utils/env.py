from __future__ import annotations

from pathlib import Path


def resolve_hf_snapshot(cache_root: str | Path) -> Path:
    root = Path(cache_root)
    if not root.exists():
        raise FileNotFoundError(f"model cache root not found: {root}")

    ref = root / "refs" / "main"
    if ref.exists():
        revision = ref.read_text(encoding="utf-8").strip()
        snapshot = root / "snapshots" / revision
        if (snapshot / "config.json").exists():
            return snapshot.resolve()

    snapshots = sorted((root / "snapshots").glob("*/config.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not snapshots:
        raise FileNotFoundError(f"no snapshot config.json found under: {root / 'snapshots'}")
    return snapshots[0].parent.resolve()


def format_bytes(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024.0 or unit == "TiB":
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{num_bytes} B"


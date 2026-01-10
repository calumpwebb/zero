from pathlib import Path


def get_cache_path(source_path: Path) -> Path:
    """Return cache path for a source file: .zr-cache/<name>.zrc"""
    cache_dir = source_path.parent / ".zr-cache"
    return cache_dir / f"{source_path.stem}.zrc"


def ensure_cache_dir(source_path: Path) -> Path:
    """Create cache directory if needed, return cache file path."""
    cache_path = get_cache_path(source_path)
    cache_path.parent.mkdir(exist_ok=True)
    return cache_path

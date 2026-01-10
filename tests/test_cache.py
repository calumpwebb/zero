import tempfile
from pathlib import Path

from zero.cache import ensure_cache_dir, get_cache_path


def test_cache_path_structure():
    """Cache path is .zr-cache/<name>.zrc relative to source."""
    source = Path("/project/src/main.zr")
    result = get_cache_path(source)
    assert result == Path("/project/src/.zr-cache/main.zrc")


def test_cache_path_nested():
    """Works for nested source files."""
    source = Path("/project/lib/utils/helper.zr")
    result = get_cache_path(source)
    assert result == Path("/project/lib/utils/.zr-cache/helper.zrc")


def test_cache_dir_created():
    """ensure_cache_dir creates .zr-cache directory if missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source = Path(tmpdir) / "main.zr"
        source.touch()

        cache_path = ensure_cache_dir(source)

        assert cache_path.parent.exists()
        assert cache_path.parent.name == ".zr-cache"
        assert cache_path.name == "main.zrc"

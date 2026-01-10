from pathlib import Path

from zero.cache import get_cache_path


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

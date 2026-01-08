"""Tests for the builtins module."""

import pytest
from zero.builtins import (
    Builtin,
    BUILTINS,
    BUILTIN_NAMES,
    BUILTIN_TYPES,
    BUILTIN_INDICES,
    BUILTIN_IMPLS,
)


class TestBuiltinRegistry:
    def test_no_duplicate_ids(self):
        ids = [b.id for b in BUILTINS]
        assert len(ids) == len(set(ids)), "Duplicate builtin IDs found"

    def test_no_duplicate_names(self):
        names = [b.name for b in BUILTINS]
        assert len(names) == len(set(names)), "Duplicate builtin names found"

    def test_print_exists(self):
        assert "print" in BUILTIN_NAMES

    def test_print_returns_int(self):
        assert BUILTIN_TYPES["print"] == "int"

    def test_print_has_index_zero(self):
        assert BUILTIN_INDICES["print"] == 0

    def test_print_impl_exists(self):
        assert 0 in BUILTIN_IMPLS
        assert callable(BUILTIN_IMPLS[0])

    def test_now_exists(self):
        assert "now" in BUILTIN_NAMES

    def test_now_returns_int(self):
        assert BUILTIN_TYPES["now"] == "int"

    def test_now_has_index_one(self):
        assert BUILTIN_INDICES["now"] == 1

    def test_now_impl_returns_timestamp(self):
        import time
        result = BUILTIN_IMPLS[1]()
        # Should be close to current time (within 1 second)
        assert abs(result - int(time.time())) < 2


class TestBuiltinLookupConsistency:
    def test_all_names_in_indices(self):
        for name in BUILTIN_NAMES:
            assert name in BUILTIN_INDICES

    def test_all_names_in_types(self):
        for name in BUILTIN_NAMES:
            assert name in BUILTIN_TYPES

    def test_all_ids_have_impls(self):
        for b in BUILTINS:
            assert b.id in BUILTIN_IMPLS

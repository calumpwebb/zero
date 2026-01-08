"""Builtin function definitions for Zero.

This is the single source of truth for all builtin functions.
Each builtin is defined once with its id, name, return type, and implementation.
"""

import time
from dataclasses import dataclass
from typing import Callable, Any


@dataclass
class Builtin:
    id: int
    name: str
    return_type: str
    impl: Callable[..., Any]


def _print_impl(value):
    """Print a value and return 0."""
    print(value)
    return 0


def _now_impl():
    """Return current Unix timestamp as int."""
    return int(time.time())


# Single source of truth for all builtins
BUILTINS = [
    Builtin(id=0, name="print", return_type="int", impl=_print_impl),
    Builtin(id=1, name="now", return_type="int", impl=_now_impl),
]

# Derived lookups
BUILTIN_NAMES = {b.name for b in BUILTINS}
BUILTIN_TYPES = {b.name: b.return_type for b in BUILTINS}
BUILTIN_INDICES = {b.name: b.id for b in BUILTINS}
BUILTIN_IMPLS = {b.id: b.impl for b in BUILTINS}

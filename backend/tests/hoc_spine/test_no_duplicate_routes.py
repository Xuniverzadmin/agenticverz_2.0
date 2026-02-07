# Layer: L4 — Tests
# AUDIENCE: INTERNAL
# Role: Guard against duplicate FastAPI (path, method) collisions.

from __future__ import annotations

from collections import Counter


def test_no_duplicate_path_method_pairs() -> None:
    from app.main import app

    pairs: list[tuple[str, str]] = []
    for route in app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None)
        if not path or not methods:
            continue
        for method in methods:
            pairs.append((path, method))

    counts = Counter(pairs)
    dupes = {pair: n for pair, n in counts.items() if n > 1}
    assert not dupes, f"Duplicate route (path, method) pairs found: {dupes}"


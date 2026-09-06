"""Rank-correlation statistics for the Phase 3 calibration protocol
(docs/scoring.md §4.2 Spearman acceptance bar, §4.3 Kendall-tau sensitivity
pass). No scipy dependency (not installed in this environment) — plain
Python, tested against known reference values.
"""
from __future__ import annotations

import math


def rank(values: list[float]) -> list[float]:
    """Average ("fractional") ranks, 1-based, ties get the mean rank of
    their tied positions."""
    n = len(values)
    order = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1
    return ranks


def pearson(x: list[float], y: list[float]) -> float:
    n = len(x)
    if n == 0:
        return float("nan")
    mx, my = sum(x) / n, sum(y) / n
    cov = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    vx = sum((xi - mx) ** 2 for xi in x)
    vy = sum((yi - my) ** 2 for yi in y)
    if vx == 0 or vy == 0:
        return float("nan")
    return cov / math.sqrt(vx * vy)


def spearman(x: list[float], y: list[float]) -> float:
    """Spearman rank correlation (Pearson correlation of the ranks)."""
    if len(x) != len(y) or len(x) < 2:
        return float("nan")
    return pearson(rank(x), rank(y))


def kendall_tau(x: list[float], y: list[float]) -> float:
    """Kendall's tau-a: (concordant - discordant) / total pairs. Pairs tied
    on either variable are excluded from both the count and the total
    (tau-a convention) rather than tie-corrected (tau-b) -- simpler, and the
    only use here (docs/scoring.md §4.3) is a stability threshold (tau >=
    0.8), not a precise inferential statistic.
    """
    n = len(x)
    if n < 2:
        return float("nan")
    concordant = 0
    discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = x[i] - x[j]
            dy = y[i] - y[j]
            if dx == 0 or dy == 0:
                continue
            if (dx > 0) == (dy > 0):
                concordant += 1
            else:
                discordant += 1
    total = concordant + discordant
    if total == 0:
        return float("nan")
    return (concordant - discordant) / total

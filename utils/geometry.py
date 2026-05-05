"""
CropBaudo – Geometry utilities.
Helper functions for spiral fitting, distance calculations, and coordinate transforms.
"""

from __future__ import annotations

import math
from typing import List, Tuple

Circle = Tuple[float, float, float]  # (x, y, radius)


def distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Euclidean distance between two 2-D points."""
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def fit_logarithmic_spiral(points: List[Tuple[float, float]]) -> Tuple[float, float]:
    """
    Fit a logarithmic spiral r = a * e^(b*theta) to a set of (x, y) points.
    Returns (a, b) spiral coefficients.
    Baudo note: crop-circle spiral arms follow logarithmic growth matching rotor-arm geometry.
    TODO: implement SciPy curve_fit based fitting.
    """
    # Placeholder: return unit spiral coefficients
    return 1.0, 0.1


def px_to_meters(px: float, dpi: float = 96.0) -> float:
    """Convert pixel distance to metres using image DPI."""
    inches = px / dpi
    return inches * 0.0254


def group_concentric(circles: List[Circle], tolerance: float = 20.0) -> List[List[Circle]]:
    """
    Group circles whose centres lie within `tolerance` pixels of each other.
    Used to identify concentric ring sets (rotor disc groups).
    """
    groups: List[List[Circle]] = []
    used = [False] * len(circles)
    for i, ci in enumerate(circles):
        if used[i]:
            continue
        group = [ci]
        used[i] = True
        for j, cj in enumerate(circles):
            if not used[j] and distance(ci[:2], cj[:2]) < tolerance:
                group.append(cj)
                used[j] = True
        groups.append(group)
    return groups

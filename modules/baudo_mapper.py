"""
CropBaudo – Phase 2: Baudo Geometry Mapper.
Maps detected circles to Umberto Baudo's mechanical components:
  - Eccentric nucleus (smallest, most offset central circle)
  - Rotating rotor discs (concentric groups, stacked disc plates)
  - Spring-linked peripheral counterweights (outermost circles)
"""

from __future__ import annotations

import math
from typing import List, Tuple, Dict, Any

from config import (
    ECCENTRIC_OFFSET_SCALE,
    DEFAULT_SPRING_K,
    DEFAULT_MASS_KG,
    BASE_RPM,
)
from utils.geometry import distance, group_concentric, px_to_meters

Circle = Tuple[float, float, float]  # (x, y, radius)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def map_baudo_geometry(circles: List[Circle]) -> Dict[str, Any]:
    """
    Accept the list of (x, y, r) circles from the CV detector and return
    a structured dict describing the full Baudo mechanical assembly.

    Baudo principle: the smallest circle whose centre is maximally offset
    from the image centroid is the eccentric nucleus driving the whole system.
    All concentric ring groups between nucleus and outermost layer form stacked
    rotor disc plates; the outermost group becomes spring-linked counterweights.
    """
    if not circles:
        return {}

    # Normalise: accept both tuple (x,y,r) and dict {"cx","cy","radius_px",...}
    def _to_tuple(c: Any) -> Circle:
        if isinstance(c, dict):
            return (c["cx"], c["cy"], c["radius_px"])
        return c

    norm_circles: List[Circle] = [_to_tuple(c) for c in circles]

    centroid = _image_centroid(norm_circles)
    nucleus = _find_eccentric_nucleus(norm_circles, centroid)

    eccentric_offset_px = _distance(nucleus[:2], centroid)
    eccentric_offset_m = px_to_meters(eccentric_offset_px)
    spring_k = compute_spring_constant(eccentric_offset_px)

    omega = BASE_RPM * 2.0 * math.pi / 60.0  # rad/s

    # Build rotor disc list with layer_index
    rotor_discs: List[Dict[str, Any]] = assign_rotor_discs(norm_circles, nucleus)

    # Build counterweight list with mass, spring_k, natural_freq
    counterweights: List[Dict[str, Any]] = assign_counterweights(norm_circles, nucleus)

    # Rotational KE: I = sum(mass * r_m^2), E = 0.5 * I * omega^2
    total_inertia = sum(
        DEFAULT_MASS_KG * px_to_meters(cw["radius"]) ** 2
        for cw in counterweights
    )
    predicted_energy_j = 0.5 * total_inertia * omega ** 2

    nat_freq = compute_natural_frequency(spring_k, sum(cw.get("mass_kg", 0.5) for cw in counterweights))

    return {
        "centroid": centroid,
        "eccentric_nucleus": {
            "x": nucleus[0],
            "y": nucleus[1],
            "radius": nucleus[2],
            "offset_px": eccentric_offset_px,
            "offset_m": eccentric_offset_m,
        },
        "rotor_discs": rotor_discs,
        "counterweights": counterweights,
        "base_rpm": BASE_RPM,
        "spring_k": spring_k,
        "predicted_energy_J": predicted_energy_j,
        "natural_frequency_hz": nat_freq,
    }


def compute_spring_constant(eccentric_offset_px: float) -> float:
    """
    Compute the spring constant required to balance the Baudo eccentric nucleus.

    Baudo principle: a larger eccentricity offset demands stiffer springs to
    maintain rotational equilibrium of the peripheral counterweight array.

    Returns DEFAULT_SPRING_K * (1 + ECCENTRIC_OFFSET_SCALE * eccentric_offset_px).
    """
    return DEFAULT_SPRING_K * (1.0 + ECCENTRIC_OFFSET_SCALE * eccentric_offset_px)


def compute_natural_frequency(spring_k: float, mass_kg: float) -> float:
    """
    Compute the natural oscillation frequency of a spring-counterweight pair.

    Baudo principle: each peripheral counterweight oscillates at its own natural
    frequency determined by its spring stiffness and mass. Matching these
    frequencies to the rotor RPM eliminates destructive resonance.

    Returns (1 / (2π)) * sqrt(k / m) in Hz.
    """
    return (1.0 / (2.0 * math.pi)) * math.sqrt(spring_k / mass_kg)


def assign_rotor_discs(circles: List[Circle], nucleus: Circle) -> List[Dict[str, Any]]:
    """
    Identify and annotate circles that form rotor disc plates in the Baudo assembly.

    Baudo principle: each concentric group between the nucleus and the outermost
    ring represents a stacked rotor disc plate. layer_index 0 is the innermost
    group immediately surrounding the nucleus.

    Returns a list of dicts with x, y, radius, layer_index, angular_velocity_rad_s.
    """
    raw = _assign_rotor_discs(circles, nucleus)
    if not raw:
        return []

    # Sort unique radii to assign layer_index (0 = smallest = innermost after nucleus)
    unique_radii = sorted(set(c[2] for c in raw))
    radius_to_layer = {r: idx for idx, r in enumerate(unique_radii)}

    omega = BASE_RPM * 2.0 * math.pi / 60.0

    result: List[Dict[str, Any]] = []
    for c in raw:
        result.append({
            "x": c[0],
            "y": c[1],
            "radius": c[2],
            "layer_index": radius_to_layer[c[2]],
            "angular_velocity_rad_s": omega,
        })
    return result


def assign_counterweights(circles: List[Circle], nucleus: Circle) -> List[Dict[str, Any]]:
    """
    Identify and annotate circles that act as spring-linked peripheral counterweights.

    Baudo principle: the outermost ring of circles (largest radius group) are
    connected via calibrated springs to absorb and redistribute eccentric forces,
    maintaining dynamic balance during rotation.

    Returns a list of dicts with x, y, radius, mass_kg, spring_k, natural_freq_hz.
    """
    raw = _assign_counterweights(circles, nucleus)
    if not raw:
        return []

    centroid = _image_centroid(circles)
    nucleus_resolved = _find_eccentric_nucleus(circles, centroid)
    eccentric_offset_px = _distance(nucleus_resolved[:2], centroid)
    spring_k = compute_spring_constant(eccentric_offset_px)
    natural_freq = compute_natural_frequency(spring_k, DEFAULT_MASS_KG)

    result: List[Dict[str, Any]] = []
    for c in raw:
        result.append({
            "x": c[0],
            "y": c[1],
            "radius": c[2],
            "mass_kg": DEFAULT_MASS_KG,
            "spring_k": spring_k,
            "natural_freq_hz": natural_freq,
        })
    return result


# ---------------------------------------------------------------------------
# Internal helpers (logic preserved from stub)
# ---------------------------------------------------------------------------

def _image_centroid(circles: List[Circle]) -> Tuple[float, float]:
    """
    Compute radius-weighted centroid of all detected circle centres.

    Baudo principle: the geometric centre of mass of the circle pattern defines
    the ideal rotation axis around which all components are balanced.
    """
    total_r = sum(c[2] for c in circles)
    cx = sum(c[0] * c[2] for c in circles) / total_r
    cy = sum(c[1] * c[2] for c in circles) / total_r
    return cx, cy


def _distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Euclidean distance between two 2-D points (pixel space)."""
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def _find_eccentric_nucleus(
    circles: List[Circle], centroid: Tuple[float, float]
) -> Circle:
    """
    Identify the eccentric nucleus: the smallest circle whose centre is
    maximally offset from the radius-weighted centroid.

    Baudo principle: this off-axis core element is the primary driver of the
    eccentric motion that powers the entire mechanical assembly.
    """
    min_r = min(c[2] for c in circles)
    small = [c for c in circles if c[2] == min_r]
    return max(small, key=lambda c: _distance(c[:2], centroid))


def _assign_rotor_discs(
    circles: List[Circle], nucleus: Circle
) -> List[Circle]:
    """
    Select circles in intermediate radius groups (between nucleus and outermost ring).

    Baudo principle: middle-radius concentric groups form the stacked rotor
    disc plates that transmit rotational energy from the eccentric nucleus
    outward to the counterweight ring.
    """
    radii = sorted(set(c[2] for c in circles))
    if len(radii) <= 2:
        return []
    mid_radii = set(radii[1:-1])
    return [c for c in circles if c[2] in mid_radii and c != nucleus]


def _assign_counterweights(
    circles: List[Circle], nucleus: Circle
) -> List[Circle]:
    """
    Select circles in the outermost radius group to serve as counterweights.

    Baudo principle: the largest-radius circles form the peripheral
    spring-linked counterweight ring that absorbs eccentric forces and
    maintains dynamic rotational balance.
    """
    max_r = max(c[2] for c in circles)
    return [c for c in circles if c[2] == max_r and c != nucleus]

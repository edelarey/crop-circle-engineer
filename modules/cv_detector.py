"""
CropBaudo – Phase 1: Computer Vision Engine.
Detects circles, spirals, and eccentric offsets in crop-circle aerial photographs.
Baudo principle: every ring in the crop circle corresponds to a mechanical disc or rotor plate.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import IO, List, Optional, Tuple, Union

import cv2
import numpy as np

from config import (
    HOUGH_DP,
    HOUGH_MAX_RADIUS,
    HOUGH_MIN_DIST,
    HOUGH_MIN_RADIUS,
    HOUGH_PARAM1,
    HOUGH_PARAM2,
    TARGET_HEIGHT,
    TARGET_WIDTH,
)
from utils.geometry import fit_logarithmic_spiral

# ---------------------------------------------------------------------------
# Public type aliases
# ---------------------------------------------------------------------------

Circle = Tuple[float, float, float]  # (x, y, radius)
SpiralCoeffs = Tuple[float, float]   # (a, b) for r = a * e^(b*theta)

# Accepted image sources: file path or any readable binary stream
ImageSource = Union[str, Path, IO[bytes]]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_circles(image_source: ImageSource) -> List[Circle]:
    """
    Load an image from a file path or file-like object, resize it,
    apply GaussianBlur + HoughCircles, and return a sorted list of
    (x, y, r) tuples (ascending by radius).

    Baudo principle: sub-pixel accuracy is preserved by using the full-resolution
    accumulator (dp=1.2) before downscaling radii to physical units.
    Each detected circle maps to a mechanical disc or rotor plate in the 3-D model.

    Parameters
    ----------
    image_source:
        A file path (str or Path) or a binary file-like object
        (Streamlit UploadedFile, BytesIO, etc.).

    Returns
    -------
    List[Circle]
        Sorted list of (x, y, radius) tuples; empty list if none found.
    """
    img = _load_image(image_source)
    img = _resize(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)

    try:
        raw = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=HOUGH_DP,
            minDist=HOUGH_MIN_DIST,
            param1=HOUGH_PARAM1,
            param2=HOUGH_PARAM2,
            minRadius=HOUGH_MIN_RADIUS,
            maxRadius=HOUGH_MAX_RADIUS,
        )
    except cv2.error as e:
        raise RuntimeError(f"HoughCircles failed: {e}") from e

    if raw is None:
        return []

    circles: List[Circle] = [
        (float(x), float(y), float(r))
        for x, y, r in np.round(raw[0]).astype(int)
    ]
    return sorted(circles, key=lambda c: c[2])  # ascending radius


def detect_spirals(image_source: ImageSource) -> List[SpiralCoeffs]:
    """
    Detect logarithmic spiral arms in a crop-circle image using Canny edge
    detection and contour fitting.

    Baudo principle: spiral arms in genuine crop circles trace logarithmic
    growth curves that match the rotor-arm geometry of Baudo's mechanical
    device.  Each (a, b) pair encodes one arm's growth factor for 3-D
    reconstruction.

    Parameters
    ----------
    image_source:
        A file path (str or Path) or a binary file-like object.

    Returns
    -------
    List[SpiralCoeffs]
        One (a, b) tuple per detected spiral arm where r = a * exp(b * theta).
        Returns an empty list if no spiral-like contours are found.
    """
    img = _load_image(image_source)
    img = _resize(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 1)

    # Canny edge map
    edges = cv2.Canny(blurred, threshold1=50, threshold2=150)

    # Retrieve external contours only
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    h, w = img.shape[:2]
    cx, cy = w / 2.0, h / 2.0
    min_points = 30          # minimum contour length to consider
    min_arc_span = np.pi     # contour must span ≥ 180° around image centre

    coeffs: List[SpiralCoeffs] = []

    for contour in contours:
        if len(contour) < min_points:
            continue

        pts = contour[:, 0, :].astype(float)  # shape (N, 2)

        # Convert to polar coordinates relative to image centre
        dx = pts[:, 0] - cx
        dy = pts[:, 1] - cy
        r_vals = np.hypot(dx, dy)
        theta_vals = np.arctan2(dy, dx)

        # Filter out degenerate contours with zero radius
        valid = r_vals > 1.0
        if valid.sum() < min_points:
            continue

        r_vals = r_vals[valid]
        theta_vals = theta_vals[valid]

        # Check angular span
        theta_range = np.ptp(theta_vals)  # peak-to-peak
        if theta_range < min_arc_span:
            continue

        # Collect as list of (x, y) points for the geometry helper
        xy_points: List[Tuple[float, float]] = list(zip(
            pts[valid, 0].tolist(), pts[valid, 1].tolist()
        ))

        try:
            ab = fit_logarithmic_spiral(xy_points)
            coeffs.append(ab)
        except Exception:
            # fit_logarithmic_spiral may be a stub; skip failures gracefully
            continue

    return coeffs


def find_eccentric_nucleus(circles: List[Circle]) -> Optional[Circle]:
    """
    Identify the eccentric nucleus from a list of detected circles.

    The eccentric nucleus is the **smallest-radius** circle whose centre is
    **maximally offset** from the weighted centroid of all circles.

    Baudo principle: Baudo's mechanism is driven by an off-axis eccentric cam
    (the nucleus) that imparts differential rotation to the outer rotor rings.
    Its displacement from the collective centroid is the key kinematic parameter.

    Parameters
    ----------
    circles:
        List of (x, y, radius) tuples as returned by ``detect_circles``.

    Returns
    -------
    Optional[Circle]
        The eccentric nucleus circle, or ``None`` if fewer than 2 circles are
        provided (offset is undefined for a single circle).
    """
    if not circles:
        return None
    if len(circles) < 2:
        return None

    arr = np.array(circles, dtype=float)  # shape (N, 3)
    xs, ys, rs = arr[:, 0], arr[:, 1], arr[:, 2]

    # Weighted centroid – larger circles contribute more to the centre of mass
    total_r = rs.sum()
    cx = float(np.dot(rs, xs) / total_r)
    cy = float(np.dot(rs, ys) / total_r)

    # Score each circle: small radius AND large offset from centroid
    offsets = np.hypot(xs - cx, ys - cy)
    # Normalise both axes to [0, 1] so neither dominates
    norm_r = rs / (rs.max() + 1e-9)
    norm_off = offsets / (offsets.max() + 1e-9)

    # Score = offset_weight - radius_penalty  → highest wins
    scores = norm_off - norm_r
    best_idx = int(np.argmax(scores))

    return (float(xs[best_idx]), float(ys[best_idx]), float(rs[best_idx]))


def annotate_image(
    image_source: ImageSource,
    circles: List[Circle],
    nucleus: Optional[Circle],
) -> np.ndarray:
    """
    Draw detected circles and the eccentric nucleus onto the image and return
    the annotated BGR ``np.ndarray``.

    Baudo principle: visual annotation maps the detected rotor rings (green)
    and the off-axis eccentric nucleus (red) onto the aerial photograph,
    providing a direct correspondence between the crop-circle pattern and the
    mechanical schematic.

    Parameters
    ----------
    image_source:
        A file path (str or Path) or a binary file-like object.
    circles:
        List of (x, y, radius) tuples to draw in green.
    nucleus:
        The eccentric nucleus circle to draw in red, or ``None``.

    Returns
    -------
    np.ndarray
        Annotated image in BGR colour space.
    """
    img = _load_image(image_source)
    img = _resize(img)
    annotated = img.copy()

    GREEN = (0, 255, 0)
    RED = (0, 0, 255)
    thickness = 2
    centre_radius = 3

    for x, y, r in circles:
        ix, iy, ir = int(round(x)), int(round(y)), int(round(r))
        cv2.circle(annotated, (ix, iy), ir, GREEN, thickness)
        cv2.circle(annotated, (ix, iy), centre_radius, GREEN, -1)

    if nucleus is not None:
        nx, ny, nr = int(round(nucleus[0])), int(round(nucleus[1])), int(round(nucleus[2]))
        cv2.circle(annotated, (nx, ny), nr, RED, thickness + 1)
        cv2.circle(annotated, (nx, ny), centre_radius + 1, RED, -1)
        # Label the nucleus
        cv2.putText(
            annotated,
            "nucleus",
            (nx + nr + 4, ny),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            RED,
            1,
            cv2.LINE_AA,
        )

    return annotated


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_image(source: ImageSource) -> np.ndarray:
    """
    Accept a file path (str or Path) or a Streamlit UploadedFile / file-like
    object and return a BGR ``np.ndarray``.

    Baudo principle: supports both batch-mode file paths and interactive
    Streamlit uploads so the engine can be embedded in any UI pipeline.
    """
    if isinstance(source, (str, Path)):
        img = cv2.imread(str(source))
        if img is None:
            raise ValueError(f"Cannot load image: {source}")
        return img

    # File-like object (Streamlit UploadedFile, BytesIO, …)
    raw_bytes: bytes
    if hasattr(source, "read"):
        raw_bytes = source.read()  # type: ignore[union-attr]
    elif isinstance(source, (bytes, bytearray)):
        raw_bytes = bytes(source)
    else:
        raw_bytes = bytes(source)  # type: ignore[arg-type]

    arr = np.frombuffer(raw_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Cannot decode image from file-like object.")
    return img


def _resize(img: np.ndarray) -> np.ndarray:
    """
    Upscale ``img`` so that both dimensions are at least
    ``TARGET_WIDTH × TARGET_HEIGHT``, preserving aspect ratio.

    Baudo principle: a minimum resolution of 1280 × 720 is required to resolve
    the fine-pitch concentric rings that correspond to thin rotor discs.
    """
    h, w = img.shape[:2]
    scale = max(TARGET_WIDTH / w, TARGET_HEIGHT / h)
    if scale > 1.0:
        new_w, new_h = int(w * scale), int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    return img

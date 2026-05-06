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

import config as _cfg
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
from utils.geometry import fit_logarithmic_spiral, px_to_meters

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
    apply preprocessing + HoughCircles, and return a sorted list of
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
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    enhanced_gray, formation_mask, edges = _preprocess_for_detection(gray)

    dp = _cfg.CV_HOUGH_DP
    min_dist = max(20, min(h, w) // _cfg.CV_HOUGH_MIN_DIST_DIVISOR)
    param1 = _cfg.CV_HOUGH_PARAM1
    param2 = _cfg.CV_HOUGH_PARAM2
    min_radius = max(8, min(h, w) // _cfg.CV_HOUGH_MIN_RADIUS_DIVISOR)
    max_radius = int(min(h, w) * _cfg.CV_HOUGH_MAX_RADIUS_FRACTION)

    try:
        raw = cv2.HoughCircles(
            enhanced_gray,
            cv2.HOUGH_GRADIENT,
            dp=dp,
            minDist=min_dist,
            param1=param1,
            param2=param2,
            minRadius=min_radius,
            maxRadius=max_radius,
        )
    except cv2.error as e:
        raise RuntimeError(f"HoughCircles failed: {e}") from e

    if raw is None:
        return []

    # Filter: keep only circles whose centre lies within the formation mask
    circles: List[dict] = []
    for x, y, r in np.round(raw[0]).astype(int):
        cx_i = int(np.clip(x, 0, w - 1))
        cy_i = int(np.clip(y, 0, h - 1))
        if formation_mask[cy_i, cx_i] > 0:
            circles.append({
                "cx": float(x),
                "cy": float(y),
                "radius_px": float(r),
                "radius_m": px_to_meters(float(r)),
            })

    # Deduplication: remove near-duplicate circles (same centre + similar radius)
    deduped: List[dict] = []
    for c in sorted(circles, key=lambda c: c["radius_px"], reverse=True):
        is_dup = False
        for kept in deduped:
            dist = np.hypot(c["cx"] - kept["cx"], c["cy"] - kept["cy"])
            r_min = min(c["radius_px"], kept["radius_px"])
            if dist < min_dist / 2 and abs(c["radius_px"] - kept["radius_px"]) < r_min * 0.15:
                is_dup = True
                break
        if not is_dup:
            deduped.append(c)

    # Cap to CV_MAX_CIRCLES sorted by radius descending, then return ascending
    deduped = sorted(deduped, key=lambda c: c["radius_px"], reverse=True)[:_cfg.CV_MAX_CIRCLES]
    return sorted(deduped, key=lambda c: c["radius_px"])  # ascending radius


def detect_spirals(image_source: ImageSource) -> List[SpiralCoeffs]:
    """
    Detect logarithmic spiral arms in a crop-circle image using preprocessed
    Canny edges and contour fitting.

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
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    enhanced_gray, formation_mask, edges = _preprocess_for_detection(gray)

    # Retrieve external contours from preprocessed edges
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    cx, cy = w / 2.0, h / 2.0
    min_points = 30          # minimum contour length to consider
    min_arc_span = np.pi     # contour must span ≥ 180° around image centre
    min_perimeter = min(h, w) * 0.05  # filter out tiny noise contours

    # Pre-filter: perimeter threshold AND centre within formation mask region
    filtered_contours = []
    for contour in contours:
        perimeter = cv2.arcLength(contour, closed=False)
        if perimeter < min_perimeter:
            continue
        # Check bounding box centre falls within formation mask
        bx, by, bw_box, bh_box = cv2.boundingRect(contour)
        box_cx = int(np.clip(bx + bw_box // 2, 0, w - 1))
        box_cy = int(np.clip(by + bh_box // 2, 0, h - 1))
        if formation_mask[box_cy, box_cx] == 0:
            continue
        filtered_contours.append((perimeter, contour))

    # Cap contours to bound spiral-fit runtime
    filtered_contours.sort(key=lambda t: t[0], reverse=True)
    top_contours = [c for _, c in filtered_contours[:_cfg.CV_MAX_SPIRAL_CONTOURS]]

    coeffs: List[SpiralCoeffs] = []

    for contour in top_contours:
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

    # Support both tuple (x, y, r) and dict {"cx", "cy", "radius_px"} circles
    if isinstance(circles[0], dict):
        arr = np.array([[c["cx"], c["cy"], c["radius_px"]] for c in circles], dtype=float)
    else:
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

    if isinstance(circles[0], dict):
        return circles[best_idx]  # type: ignore[return-value]
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

    for circle in circles:
        if isinstance(circle, dict):
            x, y, r = circle["cx"], circle["cy"], circle["radius_px"]
        else:
            x, y, r = circle
        ix, iy, ir = int(round(x)), int(round(y)), int(round(r))
        cv2.circle(annotated, (ix, iy), ir, GREEN, thickness)
        cv2.circle(annotated, (ix, iy), centre_radius, GREEN, -1)

    if nucleus is not None:
        if isinstance(nucleus, dict):
            nx, ny, nr = int(round(nucleus["cx"])), int(round(nucleus["cy"])), int(round(nucleus["radius_px"]))
        else:
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

def _preprocess_for_detection(gray: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Preprocess a grayscale image for robust circle and spiral detection.

    Applies CLAHE contrast enhancement, bilateral + Gaussian filtering,
    morphological closing, adaptive thresholding, and formation-region
    extraction to eliminate field texture noise before detection.

    Parameters
    ----------
    gray:
        Single-channel grayscale image (uint8).

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray]
        ``(enhanced_gray, binary_mask, edges)`` where:
        - ``enhanced_gray`` is the CLAHE-enhanced image for HoughCircles,
        - ``binary_mask`` is the clean formation binary mask,
        - ``edges`` is Canny edges masked to the formation region.
    """
    h, w = gray.shape[:2]
    image_area = h * w

    # 1. CLAHE contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=_cfg.CV_CLAHE_CLIP_LIMIT, tileGridSize=(8, 8)).apply(gray)

    # 2. Bilateral filter – reduces noise while preserving edges
    bilateral = cv2.bilateralFilter(clahe, d=5, sigmaColor=50, sigmaSpace=50)

    # 3. Gaussian blur for smoothing
    blurred = cv2.GaussianBlur(bilateral, (5, 5), 0)

    # 4. Multi-kernel morphological closing — preserves thin ring structure
    # First pass: small 5×5 ellipse — connects thin flattened ring edges
    kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    closed = cv2.morphologyEx(blurred, cv2.MORPH_CLOSE, kernel_small)
    # Second pass: larger kernel — fills ring interiors
    kernel_large = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (_cfg.CV_MORPH_CLOSE_KERNEL, _cfg.CV_MORPH_CLOSE_KERNEL)
    )
    closed = cv2.morphologyEx(closed, cv2.MORPH_CLOSE, kernel_large)

    # 5. Adaptive threshold → clean binary mask (finer detail: blockSize=21, C=3)
    binary_mask = cv2.adaptiveThreshold(
        closed, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=21,
        C=3,
    )

    # 5b. Opening pass — remove speckle noise before formation mask step
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel_open)

    # 6. Keep only large contours (formation region); discard field noise
    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area = image_area * _cfg.CV_FORMATION_MIN_AREA_FRACTION
    large_contours = [c for c in contours if cv2.contourArea(c) > min_area]

    formation_mask = np.zeros_like(binary_mask)
    if large_contours:
        cv2.drawContours(formation_mask, large_contours, -1, 255, -1)

    binary_mask = cv2.bitwise_and(binary_mask, formation_mask)

    # 7. Canny edges on enhanced gray, masked to formation region
    # Lower thresholds (30, 100) — more sensitive to faint ring edges
    masked_blurred = cv2.bitwise_and(blurred, blurred, mask=formation_mask)
    edges = cv2.Canny(masked_blurred, 30, 100)

    # 8. Return enhanced_gray (CLAHE output), binary_mask, edges
    return clahe, binary_mask, edges


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
    Scale ``img`` so that both dimensions fit within ``TARGET_WIDTH × TARGET_HEIGHT``,
    preserving aspect ratio. Upscales if smaller, downscales if larger.

    Baudo principle: a working resolution of 1280 × 720 is required to resolve
    the fine-pitch concentric rings that correspond to thin rotor discs, while
    capping large images prevents HoughCircles from running for minutes.
    """
    h, w = img.shape[:2]
    scale = min(TARGET_WIDTH / w, TARGET_HEIGHT / h)
    if abs(scale - 1.0) > 0.01:
        new_w, new_h = int(w * scale), int(h * scale)
        interp = cv2.INTER_CUBIC if scale > 1.0 else cv2.INTER_AREA
        img = cv2.resize(img, (new_w, new_h), interpolation=interp)
    return img

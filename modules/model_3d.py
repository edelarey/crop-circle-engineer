"""
CropBaudo – Phase 3: 3D Model Generator.
Builds a GLTF/GLB assembly from Baudo geometry parameters using trimesh.
Baudo principle: eccentric axle + layered rotor discs + spring-connected counterweights.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

import numpy as np
import trimesh

from config import GLB_FILENAME, OUTPUT_DIR
from utils.geometry import px_to_meters

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_3d_model(baudo_params: Dict[str, Any]) -> str:
    """
    Construct a 3D GLB from the mapped Baudo geometry and return the output file path.

    Baudo principle: the full device is an off-centre axle driving stacked rotor plates
    whose spring-linked counterweights store and release kinetic energy on each half-revolution.

    Assembly order:
      1. Central eccentric axle cylinder
      2. Rotor disc plates stacked along the Z axis
      3. Spring-linked counterweight spheres offset from the nucleus

    Args:
        baudo_params: Dict returned by ``map_baudo_geometry()``.

    Returns:
        Absolute path to the exported GLB file.
    """
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        out_path = os.path.join(OUTPUT_DIR, GLB_FILENAME)

        nucleus: Dict[str, Any] = baudo_params.get("eccentric_nucleus", {})
        rotor_discs: List[Dict[str, Any]] = baudo_params.get("rotor_discs", [])
        counterweights: List[Dict[str, Any]] = baudo_params.get("counterweights", [])

        scene = trimesh.Scene()

        # 1. Central eccentric axle
        axle_mesh = _build_eccentric_axle(nucleus)
        scene.add_geometry(axle_mesh, node_name="eccentric_axle")

        # 2. Rotor disc plates
        for idx, disc_mesh in enumerate(_build_rotor_discs(rotor_discs, nucleus)):
            scene.add_geometry(disc_mesh, node_name=f"rotor_disc_{idx}")

        # 3. Counterweight spheres
        for idx, cw_mesh in enumerate(_build_counterweights(counterweights, nucleus)):
            scene.add_geometry(cw_mesh, node_name=f"counterweight_{idx}")

        _scene_to_glb(scene, out_path)
        return out_path
    except Exception as e:
        raise RuntimeError(f"3D model generation failed: {e}") from e


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_eccentric_axle(nucleus: Dict[str, Any]) -> trimesh.Trimesh:
    """
    Create the central eccentric axle as a red cylinder mesh.

    Baudo principle: the off-centre (eccentric) axle is the primary driver of the device;
    its radial offset converts rotational input into alternating centrifugal pulses that
    drive the rotor plates and charge the counterweight springs.

    Args:
        nucleus: ``eccentric_nucleus`` sub-dict from ``map_baudo_geometry()``.
                 Expected keys: ``radius`` (px), ``offset_m`` (metres).

    Returns:
        A trimesh.Trimesh cylinder centred at the scene origin.
    """
    radius_px: float = float(nucleus.get("radius", 10.0))
    offset_m: float = float(nucleus.get("offset_m", 0.05))

    # Use offset_m as the scale reference; derive cylinder radius from px conversion
    radius_m: float = max(px_to_meters(radius_px), offset_m * 0.5, 0.01)
    height_m: float = radius_m * 4.0

    mesh: trimesh.Trimesh = trimesh.creation.cylinder(
        radius=radius_m,
        height=height_m,
        sections=32,
    )
    # Centre at origin (trimesh cylinder is already centred on Z)
    return _apply_material(mesh, (220, 30, 30, 255))  # red


def _build_rotor_discs(
    rotor_discs: List[Dict[str, Any]],
    nucleus: Dict[str, Any],
) -> List[trimesh.Trimesh]:
    """
    Create one flat disc (thin cylinder) per rotor disc entry.

    Baudo principle: stacked rotor plates amplify centrifugal force through additive
    angular momentum; each plate's layer_index determines its vertical position along
    the eccentric axle.

    Args:
        rotor_discs: List of rotor disc dicts from ``map_baudo_geometry()``.
                     Expected keys per entry: ``radius`` (px), ``layer_index`` (int).
        nucleus:     ``eccentric_nucleus`` sub-dict (unused but kept for API symmetry).

    Returns:
        List of trimesh.Trimesh disc meshes, each translated to its layer Z position.
    """
    disc_height_m: float = 0.01  # 1 cm thin plate
    layer_gap_m: float = 0.05    # 5 cm between layers

    meshes: List[trimesh.Trimesh] = []
    for entry in rotor_discs:
        radius_px: float = float(entry.get("radius", 10.0))
        layer_index: int = int(entry.get("layer_index", 0))

        radius_m: float = max(px_to_meters(radius_px), 0.01)
        z_offset: float = layer_index * layer_gap_m

        disc: trimesh.Trimesh = trimesh.creation.cylinder(
            radius=radius_m,
            height=disc_height_m,
            sections=64,
        )
        # Translate disc to its layer position along Z
        translation = trimesh.transformations.translation_matrix([0.0, 0.0, z_offset])
        disc.apply_transform(translation)

        meshes.append(_apply_material(disc, (30, 80, 220, 255)))  # blue

    return meshes


def _build_counterweights(
    counterweights: List[Dict[str, Any]],
    nucleus: Dict[str, Any],
) -> List[trimesh.Trimesh]:
    """
    Create one sphere mesh per counterweight entry.

    Baudo principle: spring-linked peripheral counterweights store elastic potential energy
    during the compression half-revolution and release it as kinetic energy on the expansion
    half-revolution, sustaining continuous mechanical output.

    Args:
        counterweights: List of counterweight dicts from ``map_baudo_geometry()``.
                        Expected keys per entry: ``radius`` (px), ``x`` (px), ``y`` (px).
        nucleus:        ``eccentric_nucleus`` sub-dict.
                        Expected keys: ``x`` (px), ``y`` (px).

    Returns:
        List of trimesh.Trimesh sphere meshes, each translated to its (x, y) offset position.
    """
    nucleus_x: float = float(nucleus.get("x", 0.0))
    nucleus_y: float = float(nucleus.get("y", 0.0))

    meshes: List[trimesh.Trimesh] = []
    for entry in counterweights:
        radius_px: float = float(entry.get("radius", 5.0))
        cw_x_px: float = float(entry.get("x", nucleus_x))
        cw_y_px: float = float(entry.get("y", nucleus_y))

        radius_m: float = max(px_to_meters(radius_px), 0.005)
        offset_x_m: float = px_to_meters(cw_x_px - nucleus_x)
        offset_y_m: float = px_to_meters(cw_y_px - nucleus_y)

        sphere: trimesh.Trimesh = trimesh.creation.icosphere(subdivisions=3, radius=radius_m)
        translation = trimesh.transformations.translation_matrix(
            [offset_x_m, offset_y_m, 0.0]
        )
        sphere.apply_transform(translation)

        meshes.append(_apply_material(sphere, (30, 180, 50, 255)))  # green

    return meshes


def _apply_material(
    mesh: trimesh.Trimesh,
    color_rgba: Tuple[int, int, int, int],
) -> trimesh.Trimesh:
    """
    Apply a solid RGBA vertex colour to all vertices of ``mesh`` and return it.

    Baudo principle: colour-coding components (red axle, blue rotors, green counterweights)
    mirrors Baudo's own device diagrams for rapid visual identification of energy roles.

    Args:
        mesh:       The trimesh.Trimesh to colour.
        color_rgba: (R, G, B, A) tuple with values in [0, 255].

    Returns:
        The same mesh with vertex colours applied (mutates in-place and returns).
    """
    vertex_count: int = len(mesh.vertices)
    colours: np.ndarray = np.tile(
        np.array(color_rgba, dtype=np.uint8), (vertex_count, 1)
    )
    from trimesh.visual.color import ColorVisuals  # direct submodule import avoids Pylance gap
    mesh.visual = ColorVisuals(mesh=mesh, vertex_colors=colours)
    return mesh


def _scene_to_glb(scene: trimesh.Scene, out_path: str) -> None:
    """
    Export a trimesh Scene to a binary GLTF (GLB) file.

    Baudo principle: the GLB format embeds all geometry and material data in a single
    binary file suitable for web-based 3D inspection of the Baudo device assembly.

    Args:
        scene:    The trimesh.Scene containing all Baudo component meshes.
        out_path: Filesystem path where the GLB file will be written.
    """
    scene.export(out_path, file_type="glb")

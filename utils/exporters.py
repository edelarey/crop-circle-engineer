"""
CropBaudo – Export utilities.
Handles saving annotated images, GLB files, and simulation CSV reports.
"""

from __future__ import annotations

import os
import csv
import shutil
from typing import Dict, Any

from config import OUTPUT_DIR


def save_annotated_image(img_array, filename: str = "annotated.png") -> str:
    """
    Save a NumPy BGR image array to the outputs directory.
    Returns the saved file path.
    """
    import cv2
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, filename)
    cv2.imwrite(out_path, img_array)
    return out_path


def save_simulation_csv(sim_results: Dict[str, Any], filename: str = "simulation.csv") -> str:
    """
    Write time-series simulation data to a CSV file in the outputs directory.
    Returns the saved file path.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, filename)
    keys = list(sim_results.keys())
    rows = zip(*[sim_results[k] for k in keys])
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(keys)
        writer.writerows(rows)
    return out_path


def save_baudo_params_json(baudo_params: Dict[str, Any], filename: str = "baudo_params.json") -> str:
    """Persist extracted Baudo parameters as a JSON file for reproducibility."""
    import json
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, filename)
    with open(out_path, "w") as f:
        json.dump(baudo_params, f, indent=2)
    return out_path


def batch_export_results(
    results: list[dict],
    output_dir: str = "outputs",
) -> list[str]:
    """
    Export CSV and GLB outputs for a list of pipeline results.

    For each result dict (keys: ``image_path``, ``sim_result``, ``glb_path``):
      - Writes a simulation CSV via ``physics_sim.export_sim_csv``.
      - Copies the GLB file using ``shutil.copy2`` (skips if not found).

    Args:
        results:    List of result dicts from the batch pipeline.
        output_dir: Directory to write exported files into.

    Returns:
        List of file paths that were successfully written.
    """
    from modules import physics_sim

    os.makedirs(output_dir, exist_ok=True)
    written: list[str] = []

    for result in results:
        stem = os.path.splitext(os.path.basename(result["image_path"]))[0]

        # Export simulation CSV
        csv_path = f"{output_dir}/{stem}_sim.csv"
        physics_sim.export_sim_csv(result["sim_result"], csv_path)
        written.append(csv_path)

        # Copy GLB if it exists
        glb_src: str = result["glb_path"]
        if os.path.exists(glb_src):
            glb_dst = f"{output_dir}/{stem}_model.glb"
            shutil.copy2(glb_src, glb_dst)
            written.append(glb_dst)
        else:
            print(f"[batch] GLB not found: {glb_src}")

    return written

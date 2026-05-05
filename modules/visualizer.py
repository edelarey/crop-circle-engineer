"""
modules/visualizer.py
Phase 5 – pure visualisation helpers (Composition API style, no classes).
"""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np
import plotly.graph_objects as go
import streamlit as st


def plot_rpm_curve(sim_result: dict) -> go.Figure:
    """Return a Plotly line chart of RPM vs Time."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sim_result["t"], y=sim_result["rpm"], mode="lines"))
    fig.update_layout(
        title="RPM vs Time",
        xaxis_title="Time (s)",
        yaxis_title="RPM",
    )
    return fig


def plot_energy_curve(sim_result: dict) -> go.Figure:
    """Return a Plotly line chart of Kinetic Energy vs Time."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sim_result["t"], y=sim_result["energy"], mode="lines"))
    fig.update_layout(
        title="Kinetic Energy vs Time",
        xaxis_title="Time (s)",
        yaxis_title="Energy (J)",
    )
    return fig


def plot_resonance_curve(resonance_result: dict) -> go.Figure:
    """Return a Plotly line chart of resonance amplitude vs RPM."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=resonance_result["rpm"],
            y=resonance_result["amplitude"],
            mode="lines",
        )
    )
    fig.add_vline(
        x=resonance_result["resonance_rpm"],
        line_dash="dash",
        line_color="red",
        annotation_text=f"Resonance: {resonance_result['resonance_rpm']:.1f} RPM",
    )
    fig.update_layout(
        title="Resonance Curve",
        xaxis_title="RPM",
        yaxis_title="Amplitude",
    )
    return fig


def annotated_image_to_bytes(annotated_bgr: Any) -> bytes:
    """Encode an OpenCV BGR ndarray as PNG bytes suitable for st.image."""
    success, buf = cv2.imencode(".png", annotated_bgr)
    if not success:
        raise ValueError("cv2.imencode failed to encode the annotated image.")
    return buf.tobytes()


def glb_download_button(
    glb_path: str,
    label: str = "Download 3D Model (.glb)",
) -> None:
    """Render a Streamlit download button for a GLB file."""
    import os

    if not os.path.exists(glb_path):
        st.warning(f"3D model file not found: {glb_path}")
        return

    with open(glb_path, "rb") as fh:
        glb_bytes = fh.read()

    st.download_button(
        label=label,
        data=glb_bytes,
        file_name="model.glb",
        mime="model/gltf-binary",
    )

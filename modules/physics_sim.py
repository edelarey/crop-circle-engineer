"""
CropBaudo – Phase 4: Physics Simulation.
Applies Baudo mechanical dynamics: centrifugal force, spring oscillation, gravity toggle.
Uses SciPy ODE solver to integrate equations of motion over SIM_DURATION_S.
"""

from __future__ import annotations

import csv
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from scipy.integrate import solve_ivp

from utils.geometry import px_to_meters
from config import DEFAULT_MASS_KG, DEFAULT_SPRING_K


# ---------------------------------------------------------------------------
# Normalisation – translate baudo_mapper dict → ODE-ready dict
# ---------------------------------------------------------------------------

def _normalise_params(baudo_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Accept either the spec-style baudo_params dict (with radius_m / offset_m keys)
    or the real baudo_mapper output (with pixel-space `radius` keys) and return a
    normalised dict that the ODE and resonance functions can consume safely.

    Real mapper keys used here:
      rotor_discs[i]:   x, y, radius (px), layer_index, angular_velocity_rad_s
      counterweights[i]: x, y, radius (px), mass_kg, spring_k, natural_freq_hz
      eccentric_nucleus: x, y, radius (px), offset_px, offset_m
    """
    raw_rotors: List[Dict[str, Any]] = baudo_params.get("rotor_discs", [])
    raw_cws: List[Dict[str, Any]] = baudo_params.get("counterweights", [])
    nucleus: Dict[str, Any] = baudo_params.get(
        "eccentric_nucleus", baudo_params.get("nucleus", {})
    )

    # Determine eccentric offset in metres
    offset_m: float = float(
        nucleus.get("offset_m")
        or px_to_meters(float(nucleus.get("offset_px", 0.0)))
        or 0.01
    )

    normalised_rotors: List[Dict[str, Any]] = []
    for d in raw_rotors:
        # Prefer pre-converted radius_m; fall back to px conversion
        r_m: float = float(d.get("radius_m") or px_to_meters(float(d.get("radius", 10.0))))
        normalised_rotors.append({
            "radius_m": r_m,
            "offset_m": float(d.get("offset_m", offset_m)),
            "mass_kg": float(d.get("mass_kg", DEFAULT_MASS_KG)),
        })

    normalised_cws: List[Dict[str, Any]] = []
    for cw in raw_cws:
        r_m: float = float(cw.get("radius_m") or px_to_meters(float(cw.get("radius", 10.0))))
        normalised_cws.append({
            "radius_m": r_m,
            "mass_kg": float(cw.get("mass_kg", DEFAULT_MASS_KG)),
            "spring_k": float(cw.get("spring_k", DEFAULT_SPRING_K)),
            "angle_rad": float(cw.get("angle_rad", 0.0)),
        })

    # natural_frequency_hz: use existing value or derive from first counterweight
    nat_freq: float = float(baudo_params.get("natural_frequency_hz") or 0.0)
    if nat_freq == 0.0 and normalised_cws:
        k = normalised_cws[0]["spring_k"]
        m = normalised_cws[0]["mass_kg"]
        nat_freq = (1.0 / (2.0 * math.pi)) * math.sqrt(k / m) if m > 0 else 0.0

    # dominant_radius_m
    dominant_r: float = float(baudo_params.get("dominant_radius_m") or 0.0)
    if dominant_r == 0.0 and normalised_rotors:
        dominant_r = max(d["radius_m"] for d in normalised_rotors)

    return {
        **baudo_params,
        "rotor_discs": normalised_rotors,
        "counterweights": normalised_cws,
        "natural_frequency_hz": nat_freq,
        "dominant_radius_m": dominant_r,
    }


# ---------------------------------------------------------------------------
# ODE definition
# ---------------------------------------------------------------------------

def _baudo_ode(t: float, y: List[float], params: Dict[str, Any]) -> List[float]:
    """
    Baudo rotor ODE.

    State vector y = [theta, omega]
      theta : rotor angle (rad)
      omega : angular velocity (rad/s)

    Returns [d_theta/dt, d_omega/dt].
    """
    theta, omega = y

    rotor_discs: List[Dict[str, Any]] = params.get("rotor_discs", [])
    counterweights: List[Dict[str, Any]] = params.get("counterweights", [])
    gravity_enabled: bool = params.get("gravity_enabled", True)

    g = 9.81

    # Total moment of inertia  I = Σ m_i · r_i²
    inertia: float = sum(
        d["mass_kg"] * d["radius_m"] ** 2 for d in rotor_discs
    ) or 1e-6  # guard against zero-division

    # τ_centrifugal = Σ m_i · ω² · r_i · offset_i
    tau_centrifugal: float = sum(
        d["mass_kg"] * omega ** 2 * d["radius_m"] * d["offset_m"]
        for d in rotor_discs
    )

    # τ_spring = -Σ k_j · θ
    tau_spring: float = -sum(cw["spring_k"] * theta for cw in counterweights)

    # τ_gravity = -Σ m_i · g · r_i · sin(θ)   (only when gravity enabled)
    tau_gravity: float = 0.0
    if gravity_enabled:
        tau_gravity = -sum(
            d["mass_kg"] * g * d["radius_m"] * math.sin(theta)
            for d in rotor_discs
        )

    d_theta = omega
    d_omega = (tau_centrifugal + tau_spring + tau_gravity) / inertia

    return [d_theta, d_omega]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_simulation(
    baudo_params: Dict[str, Any],
    duration_s: float = 10.0,
    dt: float = 0.01,
    gravity: bool = True,
) -> Dict[str, Any]:
    """
    Integrate Baudo dynamics using scipy.integrate.solve_ivp (RK45).

    Parameters
    ----------
    baudo_params : dict
        Output from Phase 2 baudo_mapper.
    duration_s : float
        Total simulation time in seconds.
    dt : float
        Maximum time-step for the solver.
    gravity : bool
        Enable gravity drag torque.

    Returns
    -------
    dict with keys: t, theta, omega, rpm, energy, peak_rpm,
                    peak_energy_j, natural_frequency_hz
    """
    baudo_params = _normalise_params(baudo_params)
    ode_params: Dict[str, Any] = {
        **baudo_params,
        "gravity_enabled": gravity,
    }

    # Initial conditions
    theta_0: float = 0.01   # rad
    omega_0: float = 1.0    # rad/s
    y0: List[float] = [theta_0, omega_0]

    t_span: Tuple[float, float] = (0.0, duration_s)
    t_eval: np.ndarray = np.arange(0.0, duration_s, dt)

    sol = solve_ivp(
        fun=_baudo_ode,
        t_span=t_span,
        y0=y0,
        method="RK45",
        t_eval=t_eval,
        max_step=dt,
        args=(ode_params,),
    )

    t_arr: List[float] = sol.t.tolist()
    theta_arr: List[float] = sol.y[0].tolist()
    omega_arr: List[float] = sol.y[1].tolist()

    # RPM = ω · 60 / (2π)
    rpm_arr: List[float] = [w * 60.0 / (2.0 * math.pi) for w in omega_arr]

    # Moment of inertia (scalar, time-invariant)
    rotor_discs: List[Dict[str, Any]] = baudo_params.get("rotor_discs", [])
    inertia: float = sum(d["mass_kg"] * d["radius_m"] ** 2 for d in rotor_discs) or 1e-6

    # Kinetic energy = 0.5 · I · ω²
    energy_arr: List[float] = [0.5 * inertia * w ** 2 for w in omega_arr]

    peak_rpm: float = max(rpm_arr) if rpm_arr else 0.0
    peak_energy_j: float = max(energy_arr) if energy_arr else 0.0

    return {
        "t": t_arr,
        "theta": theta_arr,
        "omega": omega_arr,
        "rpm": rpm_arr,
        "energy": energy_arr,
        "peak_rpm": peak_rpm,
        "peak_energy_j": peak_energy_j,
        "natural_frequency_hz": baudo_params.get("natural_frequency_hz", 0.0),
    }


def compute_resonance_curve(
    baudo_params: Dict[str, Any],
    rpm_range: Tuple[float, float] = (0.0, 3000.0),
    steps: int = 300,
) -> Dict[str, Any]:
    """
    Sweep steady-state forced amplitude across an RPM range.

    For each RPM compute: A = F0 / sqrt((k - m·ω²)²)
    Amplitude is clamped to 1e6.

    Returns
    -------
    dict with keys: rpm, amplitude, resonance_rpm
    """
    baudo_params = _normalise_params(baudo_params)
    rotor_discs: List[Dict[str, Any]] = baudo_params.get("rotor_discs", [])
    counterweights: List[Dict[str, Any]] = baudo_params.get("counterweights", [])

    total_mass: float = sum(d["mass_kg"] for d in rotor_discs) or 1e-9
    total_k: float = sum(cw["spring_k"] for cw in counterweights) or 1e-9

    rpm_values: List[float] = list(
        np.linspace(rpm_range[0], rpm_range[1], steps)
    )
    amplitudes: List[float] = []

    for rpm in rpm_values:
        omega: float = rpm * 2.0 * math.pi / 60.0

        # Centrifugal forcing amplitude  F0 = Σ m_i · ω² · r_i
        f0: float = sum(
            d["mass_kg"] * omega ** 2 * d["radius_m"] for d in rotor_discs
        )

        denominator: float = abs(total_k - total_mass * omega ** 2)
        if denominator < 1e-12:
            amplitude = 1e6
        else:
            amplitude = f0 / denominator

        amplitudes.append(min(amplitude, 1e6))

    # RPM at maximum amplitude
    max_idx: int = int(np.argmax(amplitudes))
    resonance_rpm: float = rpm_values[max_idx]

    return {
        "rpm": rpm_values,
        "amplitude": amplitudes,
        "resonance_rpm": resonance_rpm,
    }


def export_sim_csv(sim_result: Dict[str, Any], path: str) -> str:
    """
    Write simulation time-series to a CSV file.

    Columns: t, theta, omega, rpm, energy

    Parameters
    ----------
    sim_result : dict
        Output from run_simulation().
    path : str
        Destination file path.

    Returns
    -------
    str
        Absolute path of the written CSV file.
    """
    abs_path: str = str(Path(path).resolve())
    os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)

    rows: List[Dict[str, float]] = [
        {
            "t": t,
            "theta": theta,
            "omega": omega,
            "rpm": rpm,
            "energy": energy,
        }
        for t, theta, omega, rpm, energy in zip(
            sim_result["t"],
            sim_result["theta"],
            sim_result["omega"],
            sim_result["rpm"],
            sim_result["energy"],
        )
    ]

    fieldnames: List[str] = ["t", "theta", "omega", "rpm", "energy"]

    with open(abs_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return abs_path

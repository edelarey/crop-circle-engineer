"""
main.py – Crop Circle Engineer Streamlit UI (Phase 6)
Run with: streamlit run main.py
"""

import os

import streamlit as st

import config as cfg
from modules import cv_detector, baudo_mapper, model_3d, physics_sim, visualizer
from utils import exporters

st.set_page_config(page_title="Crop Circle Engineer", layout="wide")
st.title("🌾 Crop Circle Engineer")
st.caption("Reverse-engineer crop circles into Baudo energy-generating 3D devices")

# ---------------------------------------------------------------------------
# Sidebar (global — not inside any tab)
# ---------------------------------------------------------------------------
st.sidebar.header("⚙️ Configuration")

uploaded_file = st.sidebar.file_uploader(
    "Upload Crop Circle Image", type=["jpg", "jpeg", "png"]
)
duration_s = st.sidebar.slider("Simulation Duration (s)", 1.0, 30.0, 10.0, 0.5)
gravity = st.sidebar.checkbox("Enable Gravity", value=True)
run_btn = st.sidebar.button("🚀 Run Analysis")

with st.sidebar.expander("⚙️ Advanced CV Settings", expanded=False):
    ui_dp = st.slider(
        "Hough DP (accumulator resolution)", 0.5, 3.0, float(cfg.CV_HOUGH_DP), 0.1,
        help="Inverse ratio of accumulator resolution to image resolution. Lower = finer = more detections but slower.",
    )
    ui_param1 = st.slider(
        "param1 — Canny high threshold", 20, 300, int(cfg.CV_HOUGH_PARAM1), 5,
        help="Upper threshold for the Canny edge detector inside HoughCircles. Lower = more edges detected.",
    )
    ui_param2 = st.slider(
        "param2 — accumulator threshold", 5, 100, int(cfg.CV_HOUGH_PARAM2), 1,
        help="Accumulator threshold for circle centre candidates. Lower = more circles detected (may include false positives).",
    )
    ui_min_dist_div = st.slider(
        "Min-dist divisor", 5, 40, int(cfg.CV_HOUGH_MIN_DIST_DIVISOR), 1,
        help="Minimum distance between circle centres = image_dim ÷ this value. Higher divisor → circles can be closer together.",
    )
    ui_min_r_div = st.slider(
        "Min-radius divisor", 20, 120, int(cfg.CV_HOUGH_MIN_RADIUS_DIVISOR), 5,
        help="Minimum detectable radius = image_dim ÷ this value. Higher divisor → smaller circles detected.",
    )
    ui_max_r_frac = st.slider(
        "Max-radius fraction", 0.10, 0.60, float(cfg.CV_HOUGH_MAX_RADIUS_FRACTION), 0.01,
        help="Maximum detectable radius as a fraction of the shorter image dimension.",
    )
    ui_clahe = st.slider(
        "CLAHE clip limit", 1.0, 6.0, float(cfg.CV_CLAHE_CLIP_LIMIT), 0.5,
        help="Contrast enhancement strength. Higher = stronger local contrast boost.",
    )
    ui_morph = st.slider(
        "Morph-close kernel size", 3, 25, int(cfg.CV_MORPH_CLOSE_KERNEL), 2,
        help="Size of the morphological closing kernel (must be odd). Smaller = preserves thin rings.",
    )
    ui_min_area = st.slider(
        "Formation min-area fraction", 0.001, 0.02, float(cfg.CV_FORMATION_MIN_AREA_FRACTION), 0.001,
        help="Minimum contour area (as fraction of image) to be considered part of the formation.",
    )
    ui_max_circles = st.slider(
        "Max circles cap", 10, 100, int(cfg.CV_MAX_CIRCLES), 5,
        help="Hard cap on the number of circles returned after detection.",
    )
    show_labels = st.checkbox("Overlay Baudo labels on annotated image", value=False)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_single, tab_batch, tab_about = st.tabs(["🔍 Single Image", "📦 Batch Processing", "ℹ️ About"])

# ---------------------------------------------------------------------------
# Tab 1 — Single Image
# ---------------------------------------------------------------------------
with tab_single:
    if run_btn and uploaded_file is None:
        st.warning("Please upload a crop circle image first.")
    elif not run_btn and uploaded_file is None:
        st.info("Upload an image and click Run Analysis to begin.")
    elif run_btn and uploaded_file is not None:
        try:
            # 1. Save uploaded file to /tmp
            ext = uploaded_file.name.rsplit(".", 1)[-1]
            tmp_path = f"/tmp/crop_input.{ext}"
            with open(tmp_path, "wb") as fh:
                fh.write(uploaded_file.read())

            # 2-5. CV detection — apply UI overrides to config module before calling
            cfg.CV_HOUGH_DP = ui_dp
            cfg.CV_HOUGH_PARAM1 = ui_param1
            cfg.CV_HOUGH_PARAM2 = ui_param2
            cfg.CV_HOUGH_MIN_DIST_DIVISOR = ui_min_dist_div
            cfg.CV_HOUGH_MIN_RADIUS_DIVISOR = ui_min_r_div
            cfg.CV_HOUGH_MAX_RADIUS_FRACTION = ui_max_r_frac
            cfg.CV_CLAHE_CLIP_LIMIT = ui_clahe
            cfg.CV_MORPH_CLOSE_KERNEL = ui_morph
            cfg.CV_FORMATION_MIN_AREA_FRACTION = ui_min_area
            cfg.CV_MAX_CIRCLES = ui_max_circles

            circles = cv_detector.detect_circles(tmp_path)
            spirals = cv_detector.detect_spirals(tmp_path)
            nucleus = cv_detector.find_eccentric_nucleus(circles)
            # annotate_image signature: (image_source, circles, nucleus) — spirals detected
            # above are available for display but are not a parameter of annotate_image
            annotated_bgr = cv_detector.annotate_image(tmp_path, circles, nucleus)

            if len(circles) == 0:
                st.warning("⚠️ No circles detected. Try lowering param2 or increasing max_radius.")
            elif len(circles) < 3:
                st.info(f"ℹ️ Only {len(circles)} circle(s) detected — results may be limited. Consider a higher-resolution image.")

            # 6. Baudo mapping — signature: map_baudo_geometry(circles); nucleus/spirals
            # are re-derived internally from circles
            baudo_params = baudo_mapper.map_baudo_geometry(circles)

            # 7. 3D model
            glb_path = model_3d.build_3d_model(baudo_params)

            # 8-10. Physics simulation
            sim_result = physics_sim.run_simulation(
                baudo_params, duration_s=duration_s, gravity=gravity
            )
            resonance = physics_sim.compute_resonance_curve(baudo_params)
            os.makedirs("outputs", exist_ok=True)
            csv_path = physics_sim.export_sim_csv(sim_result, "outputs/last_sim.csv")

            # --- Row 1 ---
            display_bgr = (
                visualizer.overlay_baudo_labels(annotated_bgr, baudo_params)
                if show_labels
                else annotated_bgr
            )
            col_img, col_params = st.columns(2)
            with col_img:
                st.image(
                    visualizer.annotated_image_to_bytes(display_bgr),
                    caption="Detected Geometry",
                    width='stretch',
                )
            with col_params:
                st.subheader("Baudo Parameters")
                st.json(baudo_params)

            # --- Row 2 ---
            col_rpm, col_energy, col_res = st.columns(3)
            with col_rpm:
                st.plotly_chart(
                    visualizer.plot_rpm_curve(sim_result), width='stretch'
                )
            with col_energy:
                st.plotly_chart(
                    visualizer.plot_energy_curve(sim_result), width='stretch'
                )
            with col_res:
                st.plotly_chart(
                    visualizer.plot_resonance_curve(resonance), width='stretch'
                )

            # --- Row 3: metrics ---
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Peak RPM", f"{sim_result['peak_rpm']:.1f}")
            m2.metric("Peak Energy (J)", f"{sim_result['peak_energy_j']:.4f}")
            m3.metric("Natural Frequency (Hz)", f"{sim_result['natural_frequency_hz']:.3f}")
            m4.metric("Resonance RPM", f"{resonance['resonance_rpm']:.1f}")

            # --- Row 4: downloads ---
            dl1, dl2 = st.columns(2)
            with dl1:
                visualizer.glb_download_button(glb_path)
            with dl2:
                if os.path.exists(csv_path):
                    with open(csv_path, "rb") as fh:
                        csv_bytes = fh.read()
                    st.download_button(
                        label="Download Simulation CSV",
                        data=csv_bytes,
                        file_name="simulation.csv",
                        mime="text/csv",
                    )

        except Exception as e:
            st.error(f"Analysis failed: {e}")

# ---------------------------------------------------------------------------
# Tab 2 — Batch Processing
# ---------------------------------------------------------------------------
with tab_batch:
    st.header("Batch Processing")

    batch_files = st.file_uploader(
        "Upload multiple crop circle images",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
    )
    batch_btn = st.button("🚀 Run Batch Analysis")

    if batch_btn and batch_files:
        try:
            results = []
            progress_bar = st.progress(0)

            for i, f in enumerate(batch_files):
                tmp_path = f"/tmp/{f.name}"
                with open(tmp_path, "wb") as fh:
                    fh.write(f.read())

                circles = cv_detector.detect_circles(tmp_path)
                spirals = cv_detector.detect_spirals(tmp_path)
                nucleus = cv_detector.find_eccentric_nucleus(circles)
                baudo_params = baudo_mapper.map_baudo_geometry(circles)
                glb_path = model_3d.build_3d_model(baudo_params)
                sim_result = physics_sim.run_simulation(
                    baudo_params, duration_s=10.0, gravity=True
                )

                results.append(
                    {"image_path": tmp_path, "sim_result": sim_result, "glb_path": glb_path}
                )
                progress_bar.progress((i + 1) / len(batch_files))

            os.makedirs("outputs", exist_ok=True)
            exporters.batch_export_results(results, "outputs")
            st.success(f"Batch complete: {len(results)} images processed")

            for result, f in zip(results, batch_files):
                with st.expander(f.name):
                    st.plotly_chart(
                        visualizer.plot_rpm_curve(result["sim_result"]),
                        width='stretch',
                    )
                    st.metric("Peak RPM", f"{result['sim_result']['peak_rpm']:.1f}")

        except Exception as e:
            st.error(f"Batch failed: {e}")

    elif batch_btn and not batch_files:
        st.warning("Please upload at least one image.")

# ---------------------------------------------------------------------------
# Tab 3 — About
# ---------------------------------------------------------------------------
with tab_about:
    st.header("ℹ️ About — Crop Circle Engineer")
    st.markdown("""
    **Crop Circle Engineer** reverse-engineers aerial photographs of crop circle formations
    into parametric Baudo energy-device specifications, 3D models, and physics simulations.

    ---

    ## CV Detection Parameters

    These settings control how circles are detected from the uploaded image using OpenCV's
    `HoughCircles` algorithm and preprocessing pipeline.

    | Parameter | Config key | Description |
    |-----------|-----------|-------------|
    | **Hough DP** | `CV_HOUGH_DP` | Inverse ratio of the accumulator resolution to image resolution. `1.0` = full resolution (most detections, slowest). `2.0` = half resolution (fewer detections, faster). Typical range: 1.0–2.0. |
    | **param1 — Canny high threshold** | `CV_HOUGH_PARAM1` | Upper threshold for the internal Canny edge detector. Lower values cause more edges to be detected, which can reveal faint ring boundaries. Typical range: 40–150. |
    | **param2 — accumulator threshold** | `CV_HOUGH_PARAM2` | Threshold for a circle centre candidate in the Hough accumulator. Lower = more circles returned (including potential false positives). Higher = only the clearest circles. Typical range: 10–50. |
    | **Min-dist divisor** | `CV_HOUGH_MIN_DIST_DIVISOR` | Controls the minimum allowed distance between two detected circle centres: `min_dist = image_dim ÷ divisor`. A higher divisor allows closer circles, useful for tightly-packed concentric rings. |
    | **Min-radius divisor** | `CV_HOUGH_MIN_RADIUS_DIVISOR` | Sets the smallest detectable circle radius: `min_radius = image_dim ÷ divisor`. A higher divisor detects smaller rings. |
    | **Max-radius fraction** | `CV_HOUGH_MAX_RADIUS_FRACTION` | Sets the largest detectable circle radius as a fraction of the shorter image dimension. `0.30` = up to 30% of the image width/height. Tightening this speeds up detection significantly. |
    | **CLAHE clip limit** | `CV_CLAHE_CLIP_LIMIT` | Strength of the Contrast Limited Adaptive Histogram Equalisation applied before detection. Higher values boost local contrast more aggressively, helping reveal faint rings in low-contrast aerial photographs. |
    | **Morph-close kernel** | `CV_MORPH_CLOSE_KERNEL` | Size of the elliptical structuring element used in morphological closing. Smaller values preserve thin ring structure; larger values fill broader gaps. |
    | **Formation min-area fraction** | `CV_FORMATION_MIN_AREA_FRACTION` | Minimum contour area (as a fraction of total image area) for a region to be considered part of the crop formation. Lower values allow smaller satellite circles to be included. |
    | **Max circles cap** | `CV_MAX_CIRCLES` | Hard upper limit on the number of circles returned. Circles are sorted by radius descending before capping, so the largest rings are always retained. |

    ---

    ## Baudo Mechanical Principle

    Each detected concentric ring corresponds to one **rotor disc** in Umberto Baudo's
    documented mechanical prototype (2008–2019). The eccentric nucleus — the smallest ring
    maximally offset from the collective centroid — drives differential rotation across
    the outer rotor plates, producing the mechanical resonance modelled in the physics
    simulation.

    ---

    ## Pipeline Stages

    1. **CV Detection** — HoughCircles on CLAHE-enhanced, morphologically-closed grayscale image
    2. **Baudo Mapping** — detected rings → rotor disc specs + natural frequency
    3. **3D Model** — GLB export of the full rotor assembly
    4. **Physics Simulation** — RPM curve, energy output, resonance frequency
    """)

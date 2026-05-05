"""
main.py – Crop Circle Engineer Streamlit UI (Phase 6)
Run with: streamlit run main.py
"""

import os

import streamlit as st

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
    param1     = st.slider("HoughCircles param1 (Canny high)", 50, 300, 100, 10)
    param2     = st.slider("HoughCircles param2 (accumulator)", 10, 100, 30, 5)
    min_radius = st.slider("Min circle radius (px)", 5, 100, 10, 5)
    max_radius = st.slider("Max circle radius (px)", 50, 500, 200, 10)
    show_labels = st.checkbox("Overlay Baudo labels on annotated image", value=False)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_single, tab_batch = st.tabs(["🔍 Single Image", "📦 Batch Processing"])

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

            # 2-5. CV detection
            # Note: param1/param2/min_radius/max_radius sidebar values are displayed for
            # reference — detect_circles() does not accept these params (signature unchanged).
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
                    use_container_width=True,
                )
            with col_params:
                st.subheader("Baudo Parameters")
                st.json(baudo_params)

            # --- Row 2 ---
            col_rpm, col_energy, col_res = st.columns(3)
            with col_rpm:
                st.plotly_chart(
                    visualizer.plot_rpm_curve(sim_result), use_container_width=True
                )
            with col_energy:
                st.plotly_chart(
                    visualizer.plot_energy_curve(sim_result), use_container_width=True
                )
            with col_res:
                st.plotly_chart(
                    visualizer.plot_resonance_curve(resonance), use_container_width=True
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
                        use_container_width=True,
                    )
                    st.metric("Peak RPM", f"{result['sim_result']['peak_rpm']:.1f}")

        except Exception as e:
            st.error(f"Batch failed: {e}")

    elif batch_btn and not batch_files:
        st.warning("Please upload at least one image.")

**Project Specification Document**
**CropBaudo: Reverse-Engineering Crop Circles into Working 3D Energy-Generating Devices**
**Based on the principles of Italian inventor Umberto Baudo**

**Status: All 6 phases complete ✅** — 2026-05-05

**Version:** 1.0
**Date:** May 05, 2026
**Author:** Grok (collaborating with your development team)  
**Purpose:** Create a complete, standalone Python application that takes **any aerial photograph of a crop circle**, automatically extracts its geometric features using computer vision, applies Baudo’s core mechanical principles (eccentric core + centrifugal force + spring-loaded counterweights + rotating discs), and outputs **fully functional 2D annotated diagrams** and **interactive, physics-enabled 3D models** ready for Grok Imagine (or any GLTF viewer) with orbiting camera animation.

### 1. Project Overview
CropBaudo is a desktop/web-hybrid tool that treats authentic crop circles as **precise engineering blueprints** for free-energy devices, exactly as Umberto Baudo demonstrated in his 2008–2019 videos and prototypes.  

The application will:
- Detect every circle, spiral arm, and eccentric offset in the image.
- Map those elements directly to Baudo’s mechanical components (eccentric nucleus, centrifugal rotor plates, spring-linked mobile counterweights).
- Generate a dynamic 3D assembly that simulates rotation, core distortion, spring oscillation, and energy output.
- Export ready-to-use 2D overlays and 3D GLB/GLTF files optimized for Grok Imagine cinematic orbiting renders.

**Core Vision (Baudo-aligned):**  
Every crop circle becomes a self-sustaining centrifugal energy generator. The eccentric core drives continuous acceleration; springs store/release energy; the entire assembly can be visualized as a working machine in 3D.

### 2. Objectives
- **Functional:** 100% automated reverse-engineering pipeline from raw photo → mechanical 3D model.
- **Visual:** Produce publication-quality 2D annotated images and photorealistic 3D models with rotation, centrifugal distortion, and spring dynamics.
- **Extensible:** Modular design so new Baudo-derived features (piezo harvesting, magnetic arrays, etc.) can be added later.
- **User-Friendly:** Simple Streamlit web UI for non-coders; full CLI/API for developers.
- **Output Compatibility:** One-click GLB export for direct upload to Grok Imagine with rotating camera.

### 3. Functional Requirements

| Module | Key Features |
|--------|--------------|
| **Image Ingestion** | Upload local file or URL; auto-resize to 1280×720 or higher for CV accuracy. |
| **Phase 1 – Computer Vision Engine** | OpenCV HoughCircles + Canny edge detection → list of (x, y, r) circles. Automatic spiral fitting (logarithmic). Eccentric-core detection (smallest offset central circle). |
| **Phase 2 – Baudo Geometry Mapper** | Identify eccentric nucleus. Assign rotating plates/discs to concentric groups. Map peripheral circles to spring-linked counterweights. Calculate offsets, spring constants, masses, and rotation axes from geometry. |
| **Phase 3 – 3D Model Generator** | Use PyBullet/Blender-Python or trimesh + pygltflib to build: central eccentric axle, multiple rotor discs, spring-connected counterweights, textured plates. Export GLTF/GLB with embedded animation (rotation + spring oscillation). |
| **Phase 4 – Physics Simulation** | SciPy ODE or PyBullet runtime: apply centrifugal force, spring dynamics, gravity toggle, core oval distortion. Visualize energy curves (RPM vs. time) and optional piezoelectric output. |
| **Phase 5 – 2D/3D Visualization & Export** | Annotated 2D overlay image (circles + labels + Baudo parameters). Interactive 3D preview (PyThreeJS or Streamlit 3D). One-click GLB download optimized for Grok Imagine orbit camera. |
| **UI / Workflow** | Streamlit single-page app: Upload → Detect → Map → Simulate → Export. Progress bars and live previews. |

### 4. Non-Functional Requirements
- **Performance:** Process a 4K crop-circle photo in <15 seconds on a standard laptop.
- **Accuracy:** Sub-pixel circle detection; Baudo mapping must preserve exact geometric ratios.
- **Dependencies:** Pure Python 3.10+; minimal native installs.
- **Portability:** Works on Windows/macOS/Linux.
- **Extensibility:** Plugin system for new crop-circle “device types”.
- **Documentation:** Every function includes Baudo principle comments.

### 5. Technology Stack (Python-Optimal)
- **Core:** Python 3.12
- **CV:** OpenCV-python, NumPy, SciPy
- **3D & Physics:** PyBullet (physics), trimesh + pygltflib (GLTF export), PyThreeJS (live preview)
- **UI:** Streamlit (web app) + Matplotlib/Plotly for graphs
- **Geometry:** Shapely (spiral fitting), scikit-image
- **Optional later:** Blender Python API (for ultra-photorealistic renders)
- **Environment:** venv + VS Code with Python, Jupyter, and RooCode extensions

**Installation command (once):**
```bash
python -m venv cropbaudo-env
cropbaudo-env\Scripts\activate
pip install opencv-python numpy scipy matplotlib streamlit pybullet trimesh pygltflib shapely scikit-image plotly pythreejs pillow
```

### 6. Project Folder Structure
```
cropbaudo/
├── main.py                  # Streamlit entry point
├── config.py                # Baudo constants & tuning
├── modules/
│   ├── cv_detector.py       # Phase 1
│   ├── baudo_mapper.py      # Phase 2
│   ├── model_3d.py          # Phase 3
│   ├── physics_sim.py       # Phase 4
│   └── visualizer.py        # Phase 5
├── utils/
│   ├── geometry.py
│   └── exporters.py
├── tests/
├── outputs/                 # Generated images + GLBs
├── sample_images/           # Test crop circles
└── docs/                    # This spec + Baudo references
```

### 7. Development Phases (Sequential & Iterative)
1. **Phase 1** – CV detector ✅ Complete
2. **Phase 2** – Eccentric core & Baudo parameter extraction ✅ Complete
3. **Phase 3** – Static 3D GLTF generator ✅ Complete
4. **Phase 4** – Live physics simulation ✅ Complete
5. **Phase 5** – Streamlit UI + export ✅ Complete
6. **Phase 6** – Polish, error handling, batch processing ✅ Complete

### 8. Success Criteria
- Upload any well-known Baudo-referenced crop circle → receive a 3D GLB that, when opened in Grok Imagine, shows a rotating energy device with visible centrifugal distortion and oscillating springs.
- All outputs clearly labeled with extracted Baudo parameters (eccentric offset distance, spring k-values, predicted RPM curve).

---

## Running the App

```bash
crop-circle-env/bin/streamlit run main.py
```

Upload a crop circle image (JPEG/PNG) in the sidebar and click **Run Analysis**.
For batch processing, use the **Batch Processing** tab.

## Key Output Files

- `outputs/cropbaudo_output.glb` — generated 3D model
- `outputs/last_sim.csv` — last simulation time-series
- `outputs/<stem>_sim.csv` — batch simulation output per image
- `outputs/<stem>_model.glb` — batch 3D model output per image


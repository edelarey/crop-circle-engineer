# crop-circle-engineer

**Reverse-engineer crop circle images into Baudo-principle 3D energy-generating devices**  
*Computer vision · Physics simulation · 3D modelling*

> **Status:** All 6 phases complete ✅

---

## 🎯 Vision

Crop circles are not random art. Following Umberto Baudo's groundbreaking work (2008–2019), this application treats authentic formations as **technical blueprints** for free-energy devices powered by centrifugal force, eccentric nuclei, and oscillating spring systems.

**crop-circle-engineer** automatically:

- Detects every circle, spiral, and offset nucleus using computer vision
- Maps detected geometry to Baudo's mechanical components
- Generates downloadable GLB 3D models
- Runs physics simulations and exports time-series data
- Presents everything in a drag-and-drop Streamlit web UI

---

## ✨ Features

- **Automated Computer Vision** — OpenCV `HoughCircles` + spiral & eccentric-core detection
- **Baudo Principle Mapper** — Converts geometry into eccentric axle, rotor discs, spring constants, and counterweight masses
- **Physics Simulation** — SciPy RK45 ODE solver for RPM vs time, kinetic energy, and resonance curves
- **3D Model Export** — Full GLB (glTF 2.0) built with `trimesh`/`pygltflib`, ready to view or render
- **Streamlit Web UI** — Single-image and batch-processing tabs; one-click CSV & GLB downloads
- **Batch Processing** — Process multiple images in one run; per-image CSV and GLB outputs

---

## 🛠️ Setup

### Prerequisites

- Python 3.12

### Installation

```bash
# 1. Create virtual environment
python3.12 -m venv crop-circle-env

# 2. Install dependencies
crop-circle-env/bin/pip install -r requirements.txt

# 3. Run the app
crop-circle-env/bin/streamlit run main.py
```

Open the local URL printed by Streamlit in your browser.

---

## 🚀 Quick Start

1. Run the app (see above).
2. **Single Image tab** — Upload a JPEG or PNG aerial crop-circle photo.
3. Watch automatic detection → Baudo mapping → 3D model generation → physics simulation.
4. Download the `.glb` model or `.csv` simulation data.
5. **Batch tab** — Upload multiple images; per-image outputs land in `outputs/`.

---

## 📁 Project Structure

```
crop-circle-engineer/
├── main.py                   # Streamlit entry point (single image + batch tabs)
├── config.py                 # Baudo constants & tuning parameters
├── requirements.txt
├── modules/
│   ├── cv_detector.py        # OpenCV circle/spiral/nucleus detection
│   ├── baudo_mapper.py       # Maps geometry → Baudo mechanical params
│   ├── model_3d.py           # Builds GLB 3D model (trimesh/pygltflib)
│   ├── physics_sim.py        # SciPy RK45 ODE physics simulation
│   └── visualizer.py         # Plotly charts + Streamlit helpers
├── utils/
│   ├── geometry.py           # px_to_meters, spiral-fit helpers
│   └── exporters.py          # CSV/GLB export, batch export
├── input_images/             # Sample crop-circle photos
├── sample_images/            # Additional test images
├── outputs/                  # Generated models & simulation data (git-kept empty)
├── docs/
│   └── specification.md      # Full project specification
└── tests/
```

---

## 📖 How It Works — Baudo Principles

| Step | Module | What happens |
|------|--------|-------------|
| 1 | [`modules/cv_detector.py`](modules/cv_detector.py) | HoughCircles + spiral/nucleus detection on the uploaded image |
| 2 | [`modules/baudo_mapper.py`](modules/baudo_mapper.py) | Detected geometry → eccentric axle, rotor discs, spring constants, counterweight masses |
| 3 | [`modules/model_3d.py`](modules/model_3d.py) | Baudo params → GLB 3D model |
| 4 | [`modules/physics_sim.py`](modules/physics_sim.py) | RK45 ODE simulation → RPM, kinetic energy, resonance |
| 5 | [`modules/visualizer.py`](modules/visualizer.py) | Plotly charts rendered in Streamlit |
| 6 | [`utils/exporters.py`](utils/exporters.py) | One-click CSV & GLB download |

### Core Baudo concepts

1. **Eccentric Core** — Offset central nucleus creates continuous imbalance
2. **Centrifugal Force** — Primary energy source driving rotation
3. **Spring-Loaded Counterweights** — Mobile masses on rotor plates store and release energy
4. **Core Distortion** — Oval deformation under load produces self-acceleration

---

## 📦 Output Files

| File | Description |
|------|-------------|
| `outputs/cropbaudo_output.glb` | 3D model from last single-image run |
| `outputs/last_sim.csv` | Simulation time-series from last single-image run |
| `outputs/<stem>_model.glb` | Per-image 3D model (batch mode) |
| `outputs/<stem>_sim.csv` | Per-image simulation data (batch mode) |

---

## 🔍 Viewing GLB Output

| Tool | How |
|------|-----|
| **VSCode** | Install [glTF Tools](https://marketplace.visualstudio.com/items?itemName=kshetline.vscode-gltf) (`kshetline.vscode-gltf`), right-click `.glb` → *Preview 3D Model* |
| **Browser** | Drag & drop at [gltf-viewer.donmccurdy.com](https://gltf-viewer.donmccurdy.com) |
| **Blender** | *File → Import → glTF 2.0* |

---

## 📦 Key Dependencies

| Package | Purpose |
|---------|---------|
| `opencv-python` | Circle/spiral detection |
| `numpy` | Numerical arrays |
| `scipy` | RK45 ODE solver |
| `streamlit` | Web UI |
| `pybullet` | Rigid-body physics |
| `trimesh` | 3D mesh construction |
| `pygltflib` | GLB/glTF serialisation |
| `shapely` | 2D geometry operations |
| `scikit-image` | Image processing helpers |
| `plotly` | Interactive charts |
| `pythreejs` | Three.js bindings |
| `pillow` | Image I/O |

Full pinned list: [`requirements.txt`](requirements.txt)

---

## 3D Model Notes

The exported `.glb` file includes the full Baudo rotor assembly (eccentric axle, rotor discs, counterweights). To view with camera orbit or animation:

- **VSCode**: Install [glTF Tools](https://marketplace.visualstudio.com/items?itemName=kshetline.vscode-gltf) → right-click `.glb` → *Preview 3D Model*
- **Web**: Drag & drop at [gltf-viewer.donmccurdy.com](https://gltf-viewer.donmccurdy.com) — supports orbit, zoom, lighting
- **Blender**: File → Import → glTF 2.0 — add keyframe animation manually or via the NLA editor
- **Future**: Keyframe animation (rotation + counterweight bob) is planned for a future release using trimesh scene animation export

---

## Running Tests

```bash
crop-circle-env/bin/python -m unittest tests.test_pipeline -v
```

Tests cover: `px_to_meters` utility, Baudo mapper smoke, physics simulation smoke, resonance curve, and CSV export.

---

## 🔗 References

- Umberto Baudo conference presentations and simulation videos (2008–2019)
- Crop circle photography from Wiltshire archives

---

## 📄 License

MIT License — see [`LICENSE`](LICENSE) for details.

---

**"From crop circle to working energy device — one geometry at a time."**

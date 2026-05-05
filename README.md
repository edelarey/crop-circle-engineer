```markdown
# CropBaudo

**Reverse-engineer crop circles into working 3D energy-generating devices**  
*Based on the principles of Italian inventor Umberto Baudo*

Turn any aerial photograph of a crop circle into a precise mechanical 3D model — complete with eccentric core, centrifugal rotors, spring-loaded counterweights, and animated physics — ready for rendering in Grok Imagine with orbiting camera views.

---

## 🎯 Vision

Crop circles are not random art. Following Umberto Baudo’s groundbreaking work (2008–2019), this application treats authentic formations as **technical blueprints** for free-energy devices powered by centrifugal force, eccentric nuclei, and oscillating spring systems.

CropBaudo automatically:
- Detects every circle, spiral, and offset using computer vision
- Maps geometry to Baudo’s mechanical components
- Generates interactive 2D diagrams and physics-enabled 3D models
- Exports GLB/GLTF files optimized for Grok Imagine cinematic animations

---

## ✨ Features

- **Automated Computer Vision** — OpenCV HoughCircles + spiral & eccentric-core detection
- **Baudo Principle Mapper** — Converts geometry into eccentric axle, rotor discs, spring constants, and counterweight masses
- **Physics Simulation** — Centrifugal acceleration, core distortion, spring oscillation (SciPy / PyBullet)
- **3D Model Export** — Full GLTF/GLB with embedded animations (perfect for Grok Imagine orbiting camera)
- **Streamlit Web UI** — Drag-and-drop image upload → live preview → one-click export
- **High Accuracy** — Preserves exact geometric ratios from the original crop circle
- **Extensible** — Modular design for new device types and harvesting mechanisms

---

## 🛠️ Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR-USERNAME/cropbaudo.git
cd cropbaudo

# 2. Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Required Packages (requirements.txt)
```txt
opencv-python
numpy
scipy
matplotlib
streamlit
pybullet
trimesh
pygltflib
shapely
scikit-image
pillow
plotly
pythreejs
```

---

## 🚀 Quick Start

```bash
# Run the Streamlit web app
streamlit run main.py
```

1. Open the local URL shown in terminal
2. Upload any crop circle photo (high-resolution aerial preferred)
3. Watch automatic detection → Baudo mapping → 3D model generation
4. Download GLB file for Grok Imagine

---

## 📁 Project Structure

```
cropbaudo/
├── main.py                 # Streamlit entry point
├── config.py               # Baudo constants & tuning parameters
├── modules/
│   ├── cv_detector.py      # Phase 1: Circle & spiral detection
│   ├── baudo_mapper.py     # Phase 2: Mechanical parameter extraction
│   ├── model_3d.py         # Phase 3: 3D GLTF generation
│   ├── physics_sim.py      # Phase 4: Centrifugal & spring simulation
│   └── visualizer.py       # Phase 5: 2D/3D rendering
├── utils/
│   ├── geometry.py
│   └── exporters.py
├── sample_images/          # Test crop circles (Milk Hill, Julia Set, etc.)
├── outputs/                # Generated models & images
└── SPEC.md                 # Full project specification
```

---

## 📖 How It Works (Baudo Principles)

1. **Eccentric Core** — Offset central nucleus creates continuous imbalance
2. **Centrifugal Force** — Primary energy source driving rotation
3. **Spring-Loaded Counterweights** — Mobile masses on rotor plates store and release energy
4. **Core Distortion** — Oval deformation under load produces self-acceleration
5. **Output** — Visualized as rotating 3D energy generator with live physics

---

## 🔗 References

- Umberto Baudo conference presentations and simulation videos (2008–2019)
- Crop circle photography from Wiltshire archives
- Grok Imagine — for cinematic 3D orbiting renders

---

## 🛣️ Roadmap

- [x] Phase 1: CV Detector
- [ ] Phase 2: Baudo Mapper
- [ ] Phase 3: 3D GLTF Generator
- [ ] Phase 4: Physics Simulation
- [ ] Phase 5: Polished Streamlit UI
- [ ] Batch processing & plugin system
- [ ] Piezoelectric energy harvesting module

---

## 🤝 Contributing

We welcome contributions! Whether you're a computer vision expert, 3D modeler, or Baudo researcher — feel free to open issues or pull requests.

1. Fork the repo
2. Create a feature branch
3. Submit PR with clear description

---

## 📄 License

MIT License — feel free to use, modify, and build upon this project.

---

**“From crop circle to working energy device — one geometry at a time.”**

Made with curiosity and the spirit of discovery.  
Let's decode the blueprints together.




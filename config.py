"""
CropBaudo – Baudo constants & tuning parameters.
All values derived from Umberto Baudo's documented prototypes (2008–2019).
"""

# --- Image processing ---
TARGET_WIDTH = 1280
TARGET_HEIGHT = 720

# --- HoughCircles tuning ---
HOUGH_DP = 1.2          # Inverse ratio of accumulator resolution
HOUGH_MIN_DIST = 30     # Minimum distance between detected circle centres (px)
HOUGH_PARAM1 = 50       # Canny high threshold
HOUGH_PARAM2 = 30       # Accumulator threshold for circle detection
HOUGH_MIN_RADIUS = 10
HOUGH_MAX_RADIUS = 0    # 0 = auto

# --- Baudo mechanical constants ---
ECCENTRIC_OFFSET_SCALE = 0.05   # Fraction of main radius → eccentric displacement
DEFAULT_SPRING_K = 120.0        # N/m – spring constant for peripheral counterweights
DEFAULT_MASS_KG = 0.5           # kg  – default counterweight mass
GRAVITY = 9.81                  # m/s²
BASE_RPM = 300.0                # Starting RPM for simulation

# --- 3D model export ---
OUTPUT_DIR = "outputs"
GLB_FILENAME = "cropbaudo_output.glb"

# --- Physics simulation ---
SIM_DURATION_S = 10.0   # seconds
SIM_TIMESTEP_S = 0.01   # seconds

# CV Detection defaults
CV_HOUGH_DP = 2.0           # Larger = faster accumulator (4× speedup vs 1.2)
CV_HOUGH_PARAM1 = 80
CV_HOUGH_PARAM2 = 35
CV_CLAHE_CLIP_LIMIT = 2.0
CV_MORPH_CLOSE_KERNEL = 15
CV_FORMATION_MIN_AREA_FRACTION = 0.005  # min contour area as fraction of image
CV_MAX_CIRCLES = 50
CV_MAX_SPIRAL_CONTOURS = 20

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

# CV Detection — tuned for Wiltshire crop circle formations
CV_HOUGH_DP = 1.0            # finer accumulator for more detections
CV_HOUGH_PARAM1 = 60         # lower Canny high threshold = more edges
CV_HOUGH_PARAM2 = 15         # lower accumulator threshold = more circles detected
CV_CLAHE_CLIP_LIMIT = 3.0    # stronger contrast enhancement
CV_MORPH_CLOSE_KERNEL = 11   # slightly smaller to preserve thin ring structure
CV_FORMATION_MIN_AREA_FRACTION = 0.002   # allow smaller formation segments
CV_MAX_CIRCLES = 60          # cap at 60 (generous but bounded)
CV_MAX_SPIRAL_CONTOURS = 30  # unchanged
CV_HOUGH_MIN_DIST_DIVISOR = 15   # image_dim // 15 for minDist
CV_HOUGH_MIN_RADIUS_DIVISOR = 60  # image_dim // 60 for minRadius
CV_HOUGH_MAX_RADIUS_FRACTION = 0.30  # tightened — speeds up accumulator, still covers all rings

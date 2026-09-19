"""Application configuration for Walnut Leaf Disease Detection."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

PROJECT_NAME = "Walnut Leaf Disease Detection"
MODEL_NAME = "SwinCBAM"
MODEL_VERSION = "1.0"
MODEL_PATH = BASE_DIR / "models" / "swin_cbam_224.pth"
HISTORY_PATH = BASE_DIR / "data" / "history.json"
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
INPUT_SIZE = 224

# Keep this order the same as the working model setup.
CLASS_NAMES = [
    "Eriophyes tristriatus",
    "Healthy",
    "Macrophomina phaseolina",
    "Stephanitis pyri",
]

RECOMMENDATIONS = {
    "Eriophyes tristriatus": (
        "Symptoms may indicate mite damage such as galls, blistering, or leaf deformation. "
        "Remove heavily affected leaves and consult an agricultural specialist for suitable mite management."
    ),
    "Macrophomina phaseolina": (
        "Symptoms may indicate fungal infection with necrotic lesions or dark tissue. Remove infected leaves, "
        "improve orchard sanitation, avoid water stress, and consult an agricultural specialist."
    ),
    "Stephanitis pyri": (
        "Symptoms may indicate lace bug damage such as chlorotic speckling and discoloration. Monitor the orchard, "
        "remove severely affected leaves, and consult an agricultural specialist for pest control."
    ),
    "Healthy": (
        "The leaf appears healthy. Continue regular monitoring and maintain good orchard management practices."
    ),
}

DATASET_INFO = {
    "original_images": "3,771",
    "augmented_images": "23,788",
    "region": "Hawraman–Halabja, Iraqi Kurdistan",
    "collection_period": "Summer 2025",
    "accuracy": "96.13%",
    "precision": "96.16%",
    "recall": "96.13%",
    "f1_score": "96.12%",
}

# ===== PDF TREATMENT STEPS PATCH START =====
TREATMENT_STEPS = {
    "Eriophyes tristriatus": [
        "Isolate and inspect the affected tree or branch carefully, especially the upper and lower leaf surfaces.",
        "Remove heavily affected leaves and destroy them away from the orchard to reduce the pest source.",
        "Prune overcrowded branches to improve air movement and reduce favorable conditions for mite activity.",
        "Avoid excessive nitrogen fertilization because soft new growth can attract more pest activity.",
        "Monitor nearby walnut trees every 7 to 10 days for new symptoms or spread.",
        "If symptoms continue, consult an agricultural specialist about a suitable mite management treatment for walnut trees.",
    ],
    "Macrophomina phaseolina": [
        "Remove infected leaves and plant debris from around the tree to reduce fungal spread.",
        "Do not leave infected material in the orchard; collect and destroy it safely.",
        "Improve watering management and avoid both drought stress and poor drainage.",
        "Disinfect pruning tools after working on affected trees to reduce transfer of the pathogen.",
        "Improve soil and tree health with balanced nutrition and proper orchard sanitation.",
        "If infection is severe, consult an agricultural specialist about a suitable fungicide and field management plan.",
    ],
    "Stephanitis pyri": [
        "Inspect the underside of leaves for lace bugs, eggs, dark spots, or active feeding damage.",
        "Remove very damaged leaves when possible and keep the orchard floor clean from fallen infected leaves.",
        "Use regular monitoring because early detection makes pest control easier.",
        "Avoid unnecessary broad-spectrum insecticides because they may harm beneficial insects.",
        "Improve tree vigor with correct irrigation and balanced fertilization to reduce stress.",
        "If the pest population increases, consult an agricultural specialist for a targeted insect control method.",
    ],
    "Healthy": [
        "No disease treatment is required at this stage because the leaf appears healthy.",
        "Continue weekly monitoring for early symptoms of pests, fungal infection, or leaf discoloration.",
        "Keep the orchard clean by removing fallen leaves and unnecessary plant debris.",
        "Maintain balanced irrigation and fertilization to keep walnut trees strong.",
        "Avoid overcrowding by pruning when needed to improve sunlight and air movement.",
    ],
}
# ===== PDF TREATMENT STEPS PATCH END =====


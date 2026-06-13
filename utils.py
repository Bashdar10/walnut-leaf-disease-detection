"""Utility functions for uploads, preprocessing, history, and reports."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from torchvision import transforms

from config import (
    ALLOWED_EXTENSIONS,
    HISTORY_PATH,
    RECOMMENDATIONS,
    UPLOAD_FOLDER,
)


def ensure_directories() -> None:
    """Create required runtime directories/files when they do not exist."""
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not HISTORY_PATH.exists():
        HISTORY_PATH.write_text("[]\n", encoding="utf-8")


def allowed_file(filename: str) -> bool:
    """Return True when the filename has an accepted image extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_image(file: FileStorage) -> tuple[Path, str]:
    """Validate and save an uploaded image. Returns local path and public URL."""
    if not file or not file.filename:
        raise ValueError("No image file was provided.")

    if not allowed_file(file.filename):
        raise ValueError("Invalid file type. Please upload a JPG, JPEG, or PNG image.")

    original_name = secure_filename(file.filename)
    extension = original_name.rsplit(".", 1)[1].lower()
    unique_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}.{extension}"
    destination = UPLOAD_FOLDER / unique_name
    file.save(destination)

    try:
        with Image.open(destination) as img:
            img.verify()
        with Image.open(destination) as img:
            rgb_image = img.convert("RGB")
            rgb_image.save(destination)
    except Exception as exc:  # noqa: BLE001
        destination.unlink(missing_ok=True)
        raise ValueError("The uploaded file could not be read as a valid image.") from exc

    public_url = f"/static/uploads/{unique_name}"
    return destination, public_url


def preprocess_image(image_path):
    image = Image.open(image_path).convert("RGB")

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    return transform(image).unsqueeze(0)


def get_recommendation(class_name: str) -> str:
    """Return the management recommendation for the predicted class."""
    return RECOMMENDATIONS.get(
        class_name,
        "Consult an agricultural specialist for accurate field diagnosis and management.",
    )


def read_history() -> list[dict[str, Any]]:
    """Read prediction history from JSON."""
    ensure_directories()
    try:
        data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def write_history(history: list[dict[str, Any]]) -> None:
    """Write prediction history to JSON."""
    ensure_directories()
    HISTORY_PATH.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


def add_history_item(
    *,
    filename: str,
    image_url: str,
    predicted_class: str,
    confidence: float,
    recommendation: str,
) -> dict[str, Any]:
    """Create and save a prediction history item."""
    item = {
        "id": uuid.uuid4().hex,
        "filename": filename,
        "image_url": image_url,
        "predicted_class": predicted_class,
        "confidence": round(float(confidence), 2),
        "recommendation": recommendation,
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    history = read_history()
    history.insert(0, item)
    write_history(history[:200])
    return item




def _delete_upload_for_history_item(item: dict[str, Any]) -> None:
    """Delete the uploaded image associated with a history item, when possible."""
    image_url = str(item.get("image_url", ""))
    if not image_url.startswith("/static/uploads/"):
        return

    filename = Path(image_url).name
    if not filename:
        return

    upload_path = UPLOAD_FOLDER / filename
    try:
        upload_path.unlink(missing_ok=True)
    except Exception:
        # History deletion should not fail only because an uploaded file could not be deleted.
        pass



def delete_history_item(history_id: str, delete_upload: bool = True) -> bool:
    """Delete one prediction history item by id. Returns True if an item was removed."""
    history = read_history()
    kept_history: list[dict[str, Any]] = []
    removed_item: dict[str, Any] | None = None

    for item in history:
        if item.get("id") == history_id and removed_item is None:
            removed_item = item
        else:
            kept_history.append(item)

    if removed_item is None:
        return False

    if delete_upload:
        _delete_upload_for_history_item(removed_item)

    write_history(kept_history)
    return True



def clear_history(delete_uploads: bool = True) -> int:
    """Delete all prediction history items. Returns the number of deleted records."""
    history = read_history()

    if delete_uploads:
        for item in history:
            _delete_upload_for_history_item(item)

    write_history([])
    return len(history)

def get_history_item(history_id: str) -> dict[str, Any] | None:
    """Find one history item by id."""
    for item in read_history():
        if item.get("id") == history_id:
            return item
    return None


def get_treatment_steps(class_name: str) -> list[str]:
    """Return step-by-step treatment instructions for the predicted class."""
    try:
        from config import TREATMENT_STEPS
        return TREATMENT_STEPS.get(class_name, [])
    except Exception:
        return []


def create_pdf_report(item: dict[str, Any], lang: str | None = None) -> BytesIO:
    """Generate a PDF report that includes prediction, recommendation, and detailed treatment steps."""
    from html import escape

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    # This project is currently English-only. The lang parameter is kept for compatibility.
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    styles = getSampleStyleSheet()
    story = []

    predicted_class = item.get("predicted_class", "")
    predicted_class_display = item.get("predicted_class_display", predicted_class)

    recommendation = item.get("recommendation", "")
    if not recommendation and predicted_class:
        try:
            recommendation = get_recommendation(predicted_class)
        except Exception:
            recommendation = "Consult an agricultural specialist for accurate field diagnosis and management."

    treatment_steps = item.get("treatment_steps") or get_treatment_steps(predicted_class)

    story.append(Paragraph("Walnut Leaf Disease Detection", styles["Title"]))
    story.append(Paragraph("AI-Powered Diagnosis Result", styles["Heading2"]))
    story.append(Spacer(1, 0.2 * inch))

    rows = [
        ["Prediction ID", item.get("id", "")],
        ["Date/Time", item.get("timestamp", "")],
        ["Predicted Class", predicted_class_display],
        ["Confidence", f"{item.get('confidence', 0)}%"],
        ["Image", item.get("filename", "")],
    ]

    table = Table(rows, colWidths=[1.7 * inch, 4.7 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8f5ec")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1f2937")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Treatment / Management Recommendation", styles["Heading2"]))
    story.append(Paragraph(escape(str(recommendation)), styles["BodyText"]))
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Step-by-Step Treatment Plan", styles["Heading2"]))
    if treatment_steps:
        for index, step in enumerate(treatment_steps, start=1):
            story.append(Paragraph(f"<b>{index}.</b> {escape(str(step))}", styles["BodyText"]))
            story.append(Spacer(1, 0.08 * inch))
    else:
        story.append(Paragraph("No detailed steps are available for this class.", styles["BodyText"]))

    story.append(Spacer(1, 0.2 * inch))
    story.append(
        Paragraph(
            "Note: This system supports agricultural decision-making and does not replace professional field diagnosis.",
            styles["Italic"],
        )
    )

    doc.build(story)
    buffer.seek(0)
    return buffer

# BEGIN NON-WALNUT WARNING PATCH
def validate_walnut_leaf_candidate(image_path, min_plant_ratio: float = 0.08):
    """Return (True, '') if the uploaded image looks like a clear plant/leaf image.

    This is a safety gate before running the disease model. It helps reject
    photos that are clearly not walnut leaves, such as people, documents, rooms,
    cars, screenshots, or very unclear images.

    Important: this is not a separate trained walnut-vs-not-walnut model.
    For perfect species detection, train a second model or add a "Not walnut leaf"
    class to the dataset.
    """
    try:
        import numpy as np
        from PIL import Image

        image = Image.open(image_path).convert("RGB")
        image.thumbnail((320, 320))
        arr = np.asarray(image, dtype=np.float32) / 255.0

        if arr.size == 0:
            return False, "This image does not appear to be a walnut leaf. Please upload a clear walnut leaf image."

        red = arr[:, :, 0]
        green = arr[:, :, 1]
        blue = arr[:, :, 2]

        max_channel = arr.max(axis=2)
        min_channel = arr.min(axis=2)
        saturation = np.where(max_channel == 0, 0, (max_channel - min_channel) / max_channel)
        brightness = max_channel

        # Healthy green leaf regions.
        green_leaf = (
            (green > red * 1.04)
            & (green > blue * 1.04)
            & (saturation > 0.16)
            & (brightness > 0.16)
        )

        # Diseased/dry walnut leaves may contain yellow/brown regions.
        yellow_brown_leaf = (
            (red > 0.20)
            & (green > 0.16)
            & (red >= blue * 1.10)
            & (green >= blue * 1.05)
            & (saturation > 0.12)
            & (brightness > 0.14)
        )

        plant_like_pixels = green_leaf | yellow_brown_leaf
        plant_ratio = float(plant_like_pixels.mean())

        if plant_ratio < min_plant_ratio:
            return False, "This image does not appear to be a walnut leaf. Please upload a clear walnut leaf image."

        return True, ""

    except Exception:
        return False, "This image could not be checked. Please upload a clear walnut leaf image."


def is_prediction_confident_for_walnut(confidence: float, threshold: float = 60.0):
    """Return (True, '') if model confidence is high enough for normal prediction.

    Low confidence can mean the image is unclear, from another plant species, or
    outside the training data. The threshold can be adjusted if it is too strict.
    """
    try:
        score = float(confidence)
    except Exception:
        score = 0.0

    if score < threshold:
        return False, (
            "This image may not be a walnut leaf, or it is not clear enough for reliable diagnosis. "
            "Please upload a clear walnut leaf image."
        )

    return True, ""
# END NON-WALNUT WARNING PATCH

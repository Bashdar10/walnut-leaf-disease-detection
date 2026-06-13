"""Flask application for Walnut Leaf Disease Detection.

English-only version. Kurdish language switching and translations were removed.
"""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for
from werkzeug.exceptions import RequestEntityTooLarge

from config import (
    CLASS_NAMES,
    DATASET_INFO,
    MAX_CONTENT_LENGTH,
    MODEL_NAME,
    MODEL_VERSION,
    RECOMMENDATIONS,
)
from model import load_model
from utils import clear_history, delete_history_item
from utils import (
    add_history_item,
    create_pdf_report,
    ensure_directories,
    get_history_item,
    get_recommendation,
    preprocess_image,
    read_history,
    save_uploaded_image,
    validate_walnut_leaf_candidate,
    is_prediction_confident_for_walnut,
)

ensure_directories()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "walnut-leaf-disease-dev-key")

# English UI values are kept here only to support templates that may still use {{ ui.xxx }}.
UI_EN = {
    "project_title": "Walnut Leaf Disease Detection",
    "app_title": "Walnut Leaf Disease Detection",
    "ai_system": "AI-Powered Diagnosis System",
    "app_subtitle": "AI-Powered Diagnosis System",
    "guest_user": "Guest User",
    "dashboard": "Dashboard",
    "upload_image": "Upload Image",
    "history": "History",
    "disease_info": "Disease Info",
    "recommendations": "Recommendations",
    "about": "About",
    "upload_title": "Upload Walnut Leaf Image",
    "upload_subtitle": "Upload a clear image of the walnut leaf for disease prediction.",
    "upload_tab": "Upload Image",
    "camera_tab": "Scan with Camera",
    "scan_camera": "Scan with Camera",
    "drag_drop": "Drag & drop an image here",
    "or": "or",
    "browse_image": "Browse Image",
    "supported_formats": "Supported formats: JPG, JPEG, PNG",
    "max_size": "Max size: 10MB",
    "analyze_leaf": "Analyze Leaf",
    "remove_image": "Remove Image",
    "prediction_result": "Prediction Result",
    "prediction_empty_title": "Prediction result will appear here after analysis.",
    "prediction_empty_subtitle": "Upload or capture a walnut leaf image and click Analyze Leaf.",
    "example_images": "Example Images",
    "note": "Note",
    "note_text": "For better results, upload clear images of the upper side of the leaf captured in good lighting conditions.",
    "predicted_class": "Predicted Class",
    "confidence_score": "Confidence Score",
    "treatment_recommendation": "Treatment Recommendation",
    "upload_another": "Upload Another",
    "download_result": "Download Result",
    "open_camera": "Open Camera",
    "capture_image": "Capture Image",
    "close_camera": "Close Camera",
    "recent_history": "Prediction History",
    "no_history": "No predictions yet.",
    "disease_information": "Disease Information",
    "management_recommendations": "Management Recommendations",
    "about_project": "About This Project",
    "model_metrics": "Model Metrics",
    "dataset_info": "Dataset Information",
    "model": "Model",
    "version": "Version",
    "language": "Language",
    "english": "English",
}

CLASS_DISPLAY_NAMES_EN = {class_name: class_name for class_name in CLASS_NAMES}


# ==============================
# Load AI Model
# ==============================
try:
    model_manager = load_model()
    print("MODEL LOADED SUCCESSFULLY")
    print("MODEL TYPE:", type(model_manager))
    print("MODEL AVAILABLE:", getattr(model_manager, "available", "NO_AVAILABLE_ATTRIBUTE"))
    print("MODEL ERROR:", getattr(model_manager, "error_message", None))
except Exception as exc:  # noqa: BLE001
    model_manager = None
    print("MODEL LOAD FAILED:", exc)


@app.context_processor
def inject_globals():
    """Values available in all templates."""
    return {
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "class_names": CLASS_NAMES,
        "class_display_names": CLASS_DISPLAY_NAMES_EN,
        "lang": "en",
        "text_direction": "ltr",
        "ui": UI_EN,
        "tr": lambda key: UI_EN.get(key, key),
        "get_class_display_name": lambda class_name: class_name,
    }


# Compatibility route only. The visible language switcher is removed by the installer.
@app.get("/set-language/<lang>")
def set_language(_lang: str):
    return redirect(url_for("index"))


@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(_error):
    if request.path == "/predict":
        return jsonify({"success": False, "error": "Image is too large. Maximum upload size is 10MB."}), 413
    return render_template("error.html", message="Image is too large. Maximum upload size is 10MB."), 413


@app.errorhandler(404)
def page_not_found(_error):
    return render_template("error.html", message="The requested page was not found."), 404


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/predict")
def predict():
    """API endpoint for uploaded or camera-captured walnut leaf images."""
    global model_manager

    try:
        if "image" not in request.files:
            return jsonify({"success": False, "error": "No image was provided."}), 400

        image_file = request.files["image"]
        image_path, image_url = save_uploaded_image(image_file)
        # BEGIN NON-WALNUT WARNING PATCH
        is_leaf_candidate, leaf_warning = validate_walnut_leaf_candidate(image_path)
        if not is_leaf_candidate:
            try:
                image_path.unlink(missing_ok=True)
            except AttributeError:
                try:
                    os.remove(image_path)
                except Exception:
                    pass
            except Exception:
                pass

            return jsonify({
                "success": False,
                "error": leaf_warning,
                "image_url": image_url,
            }), 400
        # END NON-WALNUT WARNING PATCH


        if model_manager is None:
            try:
                model_manager = load_model()
                print("MODEL RELOADED SUCCESSFULLY")
            except Exception as exc:  # noqa: BLE001
                return jsonify({"success": False, "error": f"Model could not be loaded: {exc}", "image_url": image_url}), 503

        if not hasattr(model_manager, "predict"):
            return jsonify({"success": False, "error": "Model manager does not have a predict function.", "image_url": image_url}), 503

        if hasattr(model_manager, "available") and model_manager.available is False:
            return jsonify({
                "success": False,
                "error": getattr(model_manager, "error_message", "Model is not available."),
                "image_url": image_url,
            }), 503

        image_tensor = preprocess_image(image_path)
        predicted_class, confidence = model_manager.predict(image_tensor)
        # BEGIN LOW-CONFIDENCE NON-WALNUT WARNING PATCH
        is_confident, confidence_warning = is_prediction_confident_for_walnut(confidence)
        if not is_confident:
            return jsonify({
                "success": False,
                "error": confidence_warning,
                "predicted_class_raw": predicted_class,
                "confidence": confidence,
                "image_url": image_url,
            }), 400
        # END LOW-CONFIDENCE NON-WALNUT WARNING PATCH

        recommendation = get_recommendation(predicted_class)

        history_item = add_history_item(
            filename=Path(image_path).name,
            image_url=image_url,
            predicted_class=predicted_class,
            confidence=confidence,
            recommendation=recommendation,
        )

        return jsonify({
            "success": True,
            "predicted_class": predicted_class,
            "predicted_class_display": predicted_class,
            "confidence": confidence,
            "recommendation": recommendation,
            "image_url": image_url,
            "history_id": history_item["id"],
        })

    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except RuntimeError as exc:
        return jsonify({"success": False, "error": str(exc)}), 503
    except Exception as exc:  # noqa: BLE001
        app.logger.exception("Prediction failed")
        return jsonify({"success": False, "error": f"Prediction failed: {exc}"}), 500


@app.get("/history")
def history():
    return render_template("history.html", history=read_history())



@app.post("/history/delete/<history_id>")
def delete_history(history_id: str):
    """Delete one prediction from history."""
    delete_history_item(history_id)
    return redirect(url_for("history"))


@app.post("/history/clear")
def clear_history_route():
    """Delete all prediction history records."""
    clear_history()
    return redirect(url_for("history"))


@app.get("/disease-info")
def disease_info():
    disease_details = [
        {
            "name": "Eriophyes tristriatus",
            "type": "Mite-related leaf damage",
            "symptoms": "Galls, blistering, leaf deformation, and abnormal leaf surface texture.",
            "management": RECOMMENDATIONS["Eriophyes tristriatus"],
        },
        {
            "name": "Macrophomina phaseolina",
            "type": "Fungal infection",
            "symptoms": "Necrotic lesions, dark tissue, yellowing, and stressed leaf appearance.",
            "management": RECOMMENDATIONS["Macrophomina phaseolina"],
        },
        {
            "name": "Stephanitis pyri",
            "type": "Lace bug pest damage",
            "symptoms": "Chlorotic speckling, discoloration, and visible feeding damage on leaf surfaces.",
            "management": RECOMMENDATIONS["Stephanitis pyri"],
        },
        {
            "name": "Healthy",
            "type": "Normal walnut leaf condition",
            "symptoms": "Green color, no major spotting, deformation, necrosis, or pest-related damage.",
            "management": RECOMMENDATIONS["Healthy"],
        },
    ]
    return render_template("disease_info.html", disease_details=disease_details)


@app.get("/recommendations")
def recommendations():
    return render_template("recommendations.html", recommendations=RECOMMENDATIONS)


@app.get("/about")
def about():
    return render_template("about.html", dataset_info=DATASET_INFO)


@app.get("/download-result/<history_id>")
def download_result(history_id: str):
    item = get_history_item(history_id)
    if item is None:
        return render_template("error.html", message="Prediction result was not found."), 404

    try:
        pdf_buffer = create_pdf_report(item)
        filename = f"walnut_prediction_{history_id[:8]}.pdf"
        return send_file(pdf_buffer, mimetype="application/pdf", as_attachment=True, download_name=filename)
    except Exception:  # noqa: BLE001
        app.logger.exception("PDF generation failed")
        return render_template("print_report.html", item=item)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")

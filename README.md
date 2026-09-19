---
title: Walnut Leaf Disease Detection
emoji: 🌿
colorFrom: green
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Walnut Leaf Disease Detection

A Flask and PyTorch web application for detecting walnut leaf diseases using a trained SwinCBAM model.
# Walnut Leaf Disease Detection

A professional Flask-based university final project web application for walnut leaf disease detection using a trained PyTorch **SwinCBAM** model.

The system allows users to upload a walnut leaf image or scan/capture an image using the browser camera. The image is sent to a Flask API, processed with PyTorch, and the application displays the predicted disease class, confidence score, treatment/management recommendation, prediction history, and downloadable PDF result.
---
title: Walnut Leaf Disease Detection
emoji: 🌿
colorFrom: green
colorTo: emerald
sdk: docker
app_port: 7860
---
## Features

- Academic dashboard UI inspired by a dark green agricultural design.
- Drag-and-drop image upload.
- Browse image upload.
- Browser camera scan and capture.
- Flask `/predict` API endpoint.
- PyTorch model inference with `torch.no_grad()` and `model.eval()`.
- JSON prediction history in `data/history.json`.
- Downloadable PDF prediction report.
- Disease information page.
- Recommendations page.
- About page with dataset and model metrics.
- Responsive layout for laptop, tablet, and mobile.
- Safe validation for JPG, JPEG, and PNG images up to 10MB.

## Folder Structure

```text
walnut-leaf-disease-webapp/
│
├── app.py
├── model.py
├── utils.py
├── config.py
├── requirements.txt
├── runtime.txt
├── Procfile
├── README.md
├── AGENTS.md
│
├── models/
│   ├── .gitkeep
│   └── swin_cbam_224.pth
│
├── data/
│   ├── history.json
│   └── .gitkeep
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── app.js
│   ├── uploads/
│   │   └── .gitkeep
│   ├── examples/
│   │   └── .gitkeep
│   └── images/
│       └── .gitkeep
│
└── templates/
    ├── base.html
    ├── index.html
    ├── history.html
    ├── disease_info.html
    ├── recommendations.html
    ├── about.html
    ├── print_report.html
    └── error.html
```

## Dataset and Model Context

- Original images: **3,771**
- Region: **Hawraman–Halabja, Iraqi Kurdistan**
- Collection period: **Summer 2025**
- Model: **SwinCBAM**
- Test accuracy: **96.13%**
- Precision: **96.16%**
- Recall: **96.13%**
- F1-score: **96.12%**

## Supported Classes

The class order is fixed and must not be changed:

```python
[
    "Eriophyes tristriatus",
    "Macrophomina phaseolina",
    "Stephanitis pyri",
    "Healthy"
]
```

## Run Locally

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install requirements

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Add the trained model file

Place your trained model file here:

```text
models/swin_cbam_224.pth
```

### 4. Start the Flask app

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## How to Test Upload

1. Open the dashboard.
2. Drag and drop a JPG/PNG walnut leaf image or click **Browse Image**.
3. Click **Analyze Leaf**.
4. The result should appear on the right panel.

## How to Test Camera

1. Open the dashboard.
2. Choose **Scan with Camera**.
3. Click **Open Camera**.
4. Allow browser camera permission.
5. Click **Capture Image**.
6. Click **Analyze Leaf**.

Camera works on `localhost` during development and on HTTPS links after deployment.

## API Endpoint Documentation

### POST `/predict`

Accepts a multipart form-data image field named `image`.

Example response:

```json
{
  "success": true,
  "predicted_class": "Macrophomina phaseolina",
  "confidence": 98.4,
  "recommendation": "...",
  "image_url": "/static/uploads/example.jpg",
  "history_id": "..."
}
```

Error response when the model architecture or model file is missing:

```json
{
  "success": false,
  "error": "Model file or architecture is missing. Please add the trained SwinCBAM model to models/swin_cbam_224.pth and complete the model architecture in model.py."
}
```

## Model Loading Notes

The application supports these common formats:

- `torch.save(model)` full model object.
- Checkpoint with key `model_state_dict`.
- Checkpoint with key `state_dict`.
- Plain PyTorch `state_dict`.

If your `.pth` file is only a `state_dict`, you must paste/import the exact SwinCBAM architecture in `model.py` and update `build_swin_cbam_model()`.

The app intentionally does **not** fake predictions. If the model file or architecture is missing, the UI still loads, but `/predict` returns a clear error.

## Deploy to Render

1. Push this project to GitHub.
2. Go to Render and create a new **Web Service**.
3. Connect your GitHub repository.
4. Use these settings:

```text
Environment: Python
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

5. Make sure these files exist in the repository:

```text
requirements.txt
runtime.txt
Procfile
app.py
```

6. Add the model file at:

```text
models/swin_cbam_224.pth
```

If the model file is too large for GitHub, use Render persistent disk, a release asset, or a private storage download workflow. Do not expose private model URLs publicly.

## Troubleshooting

### The UI opens but prediction fails

Check that `models/swin_cbam_224.pth` exists.

### Error: model architecture is missing

Your model file is probably a `state_dict`. Paste the real SwinCBAM architecture into `model.py` and return it from `build_swin_cbam_model()`.

### Camera does not open

Use `localhost` locally or an HTTPS deployment link. Browser camera access usually does not work on plain HTTP public links.

### Upload says invalid file type

Use `.jpg`, `.jpeg`, or `.png` images only.

### Upload says file too large

The maximum upload size is 10MB.

(() => {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  let selectedFile = null;
  let selectedObjectUrl = null;
  let cameraStream = null;

  document.addEventListener("DOMContentLoaded", initDashboard);

  function initDashboard() {
    removeLegacyDuplicateResults();
    renderEmptyResult();

    const form = $("#predictionForm");
    const imageInput = $("#imageInput");
    const browseBtn = $("#browseBtn");
    const dropZone = $("#dropZone");
    const removeImageBtn = $("#removeImageBtn");
    const uploadTab = $("#uploadTab");
    const cameraTab = $("#cameraTab");
    const openCameraBtn = $("#openCameraBtn");
    const captureBtn = $("#captureBtn");
    const closeCameraBtn = $("#closeCameraBtn");

    if (!form || !imageInput) {
      console.warn("Dashboard form elements were not found.");
      return;
    }

    browseBtn?.addEventListener("click", () => imageInput.click());
    dropZone?.addEventListener("click", (event) => {
      if (event.target && event.target.id === "browseBtn") return;
      imageInput.click();
    });
    dropZone?.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        imageInput.click();
      }
    });

    imageInput.addEventListener("change", () => {
      const file = imageInput.files && imageInput.files[0];
      if (file) setSelectedFile(file);
    });

    ["dragenter", "dragover"].forEach((eventName) => {
      dropZone?.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.add("is-dragover");
      });
    });

    ["dragleave", "drop"].forEach((eventName) => {
      dropZone?.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.remove("is-dragover");
      });
    });

    dropZone?.addEventListener("drop", (event) => {
      const file = event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0];
      if (file) setSelectedFile(file);
    });

    removeImageBtn?.addEventListener("click", () => {
      resetSelectedImage();
      renderEmptyResult();
    });

    uploadTab?.addEventListener("click", () => switchMode("upload"));
    cameraTab?.addEventListener("click", () => switchMode("camera"));
    openCameraBtn?.addEventListener("click", openCamera);
    captureBtn?.addEventListener("click", captureCameraImage);
    closeCameraBtn?.addEventListener("click", closeCamera);

    form.addEventListener("submit", submitPrediction);
  }

  function removeLegacyDuplicateResults() {
    const resultCards = [...document.querySelectorAll("section, .card, .dashboard-card, .app-card")].filter((el) => {
      const heading = el.querySelector("h1,h2,h3")?.textContent?.trim().toLowerCase();
      return heading === "prediction result";
    });

    resultCards.forEach((card, index) => {
      if (index > 0) card.remove();
    });

    const container = $("#predictionResult");
    if (container) container.innerHTML = "";
  }

  function resultContainer() {
    return $("#predictionResult");
  }

  function renderEmptyResult(message) {
    const container = resultContainer();
    if (!container) return;

    const title = message || "Prediction result will appear here after analysis.";
    const subtitle = message ? "Please wait until the analysis finishes." : "Upload or capture a walnut leaf image and click Analyze Leaf.";

    container.innerHTML = `
      <div class="result-empty-state">
        <div class="empty-leaf-icon">🍃</div>
        <h3>${escapeHtml(title)}</h3>
        <p>${escapeHtml(subtitle)}</p>
      </div>
    `;
  }

  function switchMode(mode) {
    const uploadPanel = $("#uploadPanel");
    const cameraPanel = $("#cameraPanel");
    const uploadTab = $("#uploadTab");
    const cameraTab = $("#cameraTab");

    if (mode === "camera") {
      uploadPanel?.classList.remove("active");
      cameraPanel?.classList.add("active");
      uploadTab?.classList.remove("active");
      cameraTab?.classList.add("active");
    } else {
      cameraPanel?.classList.remove("active");
      uploadPanel?.classList.add("active");
      cameraTab?.classList.remove("active");
      uploadTab?.classList.add("active");
      closeCamera();
    }
  }

  function setSelectedFile(file) {
    if (!file || !file.type || !file.type.startsWith("image/")) {
      showWarning("Invalid File", "Please choose a JPG, JPEG, or PNG image file.");
      return;
    }

    selectedFile = file;
    renderEmptyResult();

    const card = $("#selectedFileCard");
    const preview = $("#selectedPreview");
    const name = $("#selectedFileName");
    const status = $("#selectedFileStatus");
    const analyzeBtn = $("#analyzeBtn");
    const imageInput = $("#imageInput");

    if (selectedObjectUrl) URL.revokeObjectURL(selectedObjectUrl);
    selectedObjectUrl = URL.createObjectURL(file);

    if (preview) preview.src = selectedObjectUrl;
    if (name) name.textContent = file.name || "captured_image.jpg";
    if (status) status.textContent = "Ready for analysis.";
    if (card) card.hidden = false;
    if (analyzeBtn) {
      analyzeBtn.disabled = false;
      analyzeBtn.textContent = "Analyze Leaf";
    }

    // Keep file input clean for camera-captured files, but do not break normal upload.
    if (imageInput && file.name.startsWith("camera_leaf_")) imageInput.value = "";
  }

  function resetSelectedImage() {
    selectedFile = null;
    const imageInput = $("#imageInput");
    const card = $("#selectedFileCard");
    const preview = $("#selectedPreview");
    const name = $("#selectedFileName");
    const status = $("#selectedFileStatus");
    const analyzeBtn = $("#analyzeBtn");

    if (imageInput) imageInput.value = "";
    if (preview) preview.removeAttribute("src");
    if (name) name.textContent = "No image selected";
    if (status) status.textContent = "Ready for analysis.";
    if (card) card.hidden = true;
    if (analyzeBtn) {
      analyzeBtn.disabled = true;
      analyzeBtn.textContent = "Analyze Leaf";
    }

    if (selectedObjectUrl) URL.revokeObjectURL(selectedObjectUrl);
    selectedObjectUrl = null;
  }

  async function openCamera() {
    try {
      cameraStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: false,
      });

      const video = $("#cameraVideo");
      const placeholder = $("#cameraPlaceholder");
      if (video) video.srcObject = cameraStream;
      if (placeholder) placeholder.style.display = "none";

      setButtonState("#captureBtn", false);
      setButtonState("#closeCameraBtn", false);
      setButtonState("#openCameraBtn", true);
    } catch (error) {
      showWarning("Camera Error", "Camera could not be opened. Please allow camera permission or upload an image instead.");
    }
  }

  function captureCameraImage() {
    const video = $("#cameraVideo");
    const canvas = $("#cameraCanvas");
    if (!video || !canvas || !video.videoWidth || !video.videoHeight) {
      showWarning("Camera Warning", "Camera is not ready yet. Please wait a moment and try again.");
      return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      if (!blob) {
        showWarning("Camera Warning", "The captured image could not be prepared. Please try again.");
        return;
      }
      const file = new File([blob], `camera_leaf_${Date.now()}.jpg`, { type: "image/jpeg" });
      setSelectedFile(file);
      closeCamera();
      switchMode("upload");
    }, "image/jpeg", 0.92);
  }

  function closeCamera() {
    if (cameraStream) {
      cameraStream.getTracks().forEach((track) => track.stop());
      cameraStream = null;
    }

    const video = $("#cameraVideo");
    const placeholder = $("#cameraPlaceholder");
    if (video) video.srcObject = null;
    if (placeholder) placeholder.style.display = "flex";

    setButtonState("#captureBtn", true);
    setButtonState("#closeCameraBtn", true);
    setButtonState("#openCameraBtn", false);
  }

  function setButtonState(selector, disabled) {
    const button = $(selector);
    if (button) button.disabled = disabled;
  }

  async function submitPrediction(event) {
    event.preventDefault();

    if (!selectedFile) {
      showWarning("No Image Selected", "Please upload or capture a clear walnut leaf image first.");
      return;
    }

    const analyzeBtn = $("#analyzeBtn");
    const status = $("#selectedFileStatus");

    renderEmptyResult("Analyzing image...");
    if (status) status.textContent = "Analyzing image...";

    if (analyzeBtn) {
      analyzeBtn.disabled = true;
      analyzeBtn.textContent = "Analyzing...";
    }

    const formData = new FormData();
    formData.append("image", selectedFile, selectedFile.name || "walnut_leaf.jpg");

    try {
      const response = await fetch("/predict", {
        method: "POST",
        body: formData,
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok || data.success === false) {
        const message = data.error || "This image could not be analyzed. Please upload a clear walnut leaf image.";
        showWarning("Image Warning", message);
        if (status) status.textContent = "Analysis stopped. Please choose another image.";
        return;
      }

      showPredictionResult(data);
      if (status) status.textContent = "Analysis completed.";
    } catch (error) {
      showWarning("Connection Error", "The prediction request failed. Please make sure the Flask server is running and try again.");
      if (status) status.textContent = "Connection error.";
    } finally {
      if (analyzeBtn) {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = "Analyze Leaf";
      }
    }
  }

  function showWarning(title, message) {
    const container = resultContainer();
    if (!container) return;

    container.innerHTML = `
      <div class="friendly-warning-card">
        <div class="friendly-warning-icon">!</div>
        <div>
          <h3>${escapeHtml(title)}</h3>
          <p>${escapeHtml(message)}</p>
        </div>
      </div>
    `;
  }

  function showPredictionResult(data) {
    const container = resultContainer();
    if (!container) return;

    const imageUrl = data.image_url || "";
    const predictedClass = data.predicted_class_display || data.predicted_class || "Unknown";
    const confidenceNumber = Number(data.confidence || 0);
    const confidence = confidenceNumber.toFixed(2);
    const recommendation = data.recommendation || "No recommendation available.";
    const historyId = data.history_id || "";

    container.innerHTML = `
      ${imageUrl ? `<div class="result-image-box"><img src="${escapeAttribute(imageUrl)}" alt="Analyzed leaf image"></div>` : ""}
      <div class="result-info-card">
        <span>Predicted Class</span>
        <h3>${escapeHtml(predictedClass)}</h3>
        <span>Confidence Score</span>
        <strong>${confidence}%</strong>
        <div class="confidence-track"><div style="width: ${Math.max(0, Math.min(100, confidenceNumber))}%"></div></div>
      </div>
      <div class="result-info-card">
        <h3>Treatment Recommendation</h3>
        <p>${escapeHtml(recommendation)}</p>
      </div>
      ${historyId ? `<div class="download-row"><a class="outline-action download-action" href="/download-result/${escapeAttribute(historyId)}">Download Result</a></div>` : ""}
    `;
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function escapeAttribute(value) {
    return escapeHtml(value).replaceAll("`", "&#096;");
  }
})();

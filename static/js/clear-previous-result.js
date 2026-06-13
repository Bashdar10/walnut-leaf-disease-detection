(function () {
  "use strict";

  function textIncludes(el, text) {
    return (el.textContent || "").toLowerCase().includes(text.toLowerCase());
  }

  function findPredictionCard() {
    const direct = document.getElementById("resultCard") ||
      document.getElementById("predictionResult") ||
      document.querySelector(".fixed-result-card") ||
      document.querySelector(".prediction-result") ||
      document.querySelector(".result-card") ||
      document.querySelector(".result-panel");

    if (direct) return direct;

    const headings = Array.from(document.querySelectorAll("h1,h2,h3,h4,.section-title,.card-title"));
    const heading = headings.find((el) => textIncludes(el, "Prediction Result"));
    if (!heading) return null;
    return heading.closest(".card,.panel,section,article,div") || heading.parentElement;
  }

  function findEmptyResult(card) {
    return document.getElementById("emptyResult") ||
      document.querySelector(".fixed-empty-result") ||
      document.querySelector(".empty-result") ||
      (card ? Array.from(card.querySelectorAll("div")).find((el) => textIncludes(el, "Prediction result will appear")) : null);
  }

  function findResultContent(card) {
    return document.getElementById("resultContent") ||
      document.querySelector(".fixed-result-content") ||
      document.querySelector(".result-content") ||
      document.querySelector(".prediction-content") ||
      (card ? card.querySelector("[data-result-content]") : null);
  }

  function clearFriendlyMessages() {
    document.querySelectorAll(".friendly-alert-box, .friendly-toast-wrap, .inline-error, .toast, .alert, .error-message").forEach((el) => {
      if ((el.textContent || "").toLowerCase().includes("warning") ||
          (el.textContent || "").toLowerCase().includes("walnut") ||
          (el.textContent || "").toLowerCase().includes("error") ||
          el.classList.contains("friendly-alert-box") ||
          el.classList.contains("friendly-toast-wrap")) {
        el.remove();
      }
    });
  }

  function clearPredictionPanel() {
    const card = findPredictionCard();
    const emptyResult = findEmptyResult(card);
    const resultContent = findResultContent(card);

    clearFriendlyMessages();

    if (resultContent) {
      resultContent.innerHTML = "";
      resultContent.classList.add("hidden");
      resultContent.style.display = "none";
    }

    if (emptyResult) {
      emptyResult.classList.remove("hidden");
      emptyResult.style.display = "";
    }

    if (card) {
      card.querySelectorAll(
        ".fixed-result-image, .fixed-confidence-box, .fixed-recommend-box, .fixed-result-actions, " +
        ".result-image, .confidence-box, .recommend-box, .result-actions, " +
        ".prediction-details, .prediction-output, .download-result, .result-download"
      ).forEach((el) => el.remove());
    }
  }

  function markNewImageSelected() {
    clearPredictionPanel();
  }

  document.addEventListener("change", function (event) {
    const target = event.target;
    if (target && target.matches && target.matches("input[type='file'], #imageInput")) {
      markNewImageSelected();
    }
  }, true);

  document.addEventListener("drop", function (event) {
    if (event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files.length > 0) {
      markNewImageSelected();
    }
  }, true);

  document.addEventListener("click", function (event) {
    const target = event.target;
    if (!target || !target.closest) return;

    if (target.closest("#removeImage, .remove-image, [data-remove-image]")) {
      clearPredictionPanel();
    }

    if (target.closest("#captureImage, .capture-image, [data-capture-image]")) {
      setTimeout(markNewImageSelected, 150);
    }

    if (target.closest("#uploadAnotherButton, .upload-another, [data-upload-another]")) {
      clearPredictionPanel();
    }
  }, true);

  document.addEventListener("submit", function (event) {
    const form = event.target;
    if (form && (form.id === "predictForm" || form.matches("form[action*='predict'], form[data-predict-form]"))) {
      clearPredictionPanel();
    }
  }, true);

  // Make it available for app.js or future scripts.
  window.clearPredictionPanel = clearPredictionPanel;
})();

(function () {
  "use strict";

  const originalAlert = window.alert ? window.alert.bind(window) : null;
  let toastTimer = null;

  function normalizeMessage(message) {
    return String(message || "Something went wrong. Please try again.").trim();
  }

  function isErrorLike(message) {
    const text = normalizeMessage(message).toLowerCase();
    return (
      text.includes("not appear") ||
      text.includes("not a walnut") ||
      text.includes("please upload") ||
      text.includes("error") ||
      text.includes("failed") ||
      text.includes("invalid") ||
      text.includes("too large") ||
      text.includes("model") ||
      text.includes("prediction") ||
      text.includes("image")
    );
  }

  function findPredictionCard() {
    const headings = Array.from(document.querySelectorAll("h1,h2,h3,h4,.section-title,.card-title"));
    const heading = headings.find((el) => (el.textContent || "").toLowerCase().includes("prediction result"));
    if (heading) {
      return heading.closest(".card,.panel,.result-card,.prediction-card,section,article,div") || heading.parentElement;
    }

    return (
      document.querySelector("#resultCard") ||
      document.querySelector("#predictionResult") ||
      document.querySelector(".prediction-result") ||
      document.querySelector(".result-panel") ||
      document.querySelector(".result-card")
    );
  }

  function createInlineAlert(message, title) {
    const msg = normalizeMessage(message);
    const existing = document.querySelector(".friendly-alert-box");
    if (existing) existing.remove();

    const box = document.createElement("div");
    box.className = "friendly-alert-box";
    box.setAttribute("role", "alert");
    box.innerHTML = `
      <div class="friendly-alert-icon">!</div>
      <div class="friendly-alert-content">
        <div class="friendly-alert-title">${title || "Image Warning"}</div>
        <div class="friendly-alert-message"></div>
      </div>
      <button type="button" class="friendly-alert-close" aria-label="Close">×</button>
    `;
    box.querySelector(".friendly-alert-message").textContent = msg;
    box.querySelector(".friendly-alert-close").addEventListener("click", () => box.remove());

    const card = findPredictionCard();
    if (card) {
      const heading = Array.from(card.querySelectorAll("h1,h2,h3,h4,.section-title,.card-title"))
        .find((el) => (el.textContent || "").toLowerCase().includes("prediction result"));
      if (heading && heading.parentNode) {
        heading.insertAdjacentElement("afterend", box);
      } else {
        card.prepend(box);
      }
    } else {
      document.body.prepend(box);
    }
  }

  function createToast(message, title, type) {
    const msg = normalizeMessage(message);
    let wrap = document.querySelector(".friendly-toast-wrap");
    if (!wrap) {
      wrap = document.createElement("div");
      wrap.className = "friendly-toast-wrap";
      document.body.appendChild(wrap);
    }

    wrap.innerHTML = "";
    const toast = document.createElement("div");
    toast.className = `friendly-toast ${type || "error"}`;
    toast.setAttribute("role", "alert");
    toast.innerHTML = `
      <div class="friendly-alert-icon">!</div>
      <div class="friendly-alert-content">
        <div class="friendly-alert-title">${title || "Image Warning"}</div>
        <div class="friendly-alert-message"></div>
      </div>
      <button type="button" class="friendly-toast-close" aria-label="Close">×</button>
    `;
    toast.querySelector(".friendly-alert-message").textContent = msg;
    toast.querySelector(".friendly-toast-close").addEventListener("click", () => wrap.remove());
    wrap.appendChild(toast);

    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      if (wrap && wrap.parentNode) wrap.remove();
    }, 6500);
  }

  window.showFriendlyError = function (message, title) {
    createInlineAlert(message, title || "Image Warning");
    createToast(message, title || "Image Warning", "error");
  };

  window.showFriendlyNotice = function (message, title) {
    createToast(message, title || "Notice", "success");
  };

  // Replace ugly browser alert() with a beautiful label + toast.
  window.alert = function (message) {
    if (isErrorLike(message)) {
      window.showFriendlyError(message, "Image Warning");
      return;
    }

    if (originalAlert) {
      originalAlert(message);
    } else {
      window.showFriendlyNotice(message, "Notice");
    }
  };

  // Catch common result error containers if the app writes errors to the DOM.
  document.addEventListener("DOMContentLoaded", function () {
    const params = new URLSearchParams(window.location.search);
    const error = params.get("error") || params.get("message");
    if (error) window.showFriendlyError(error, "Image Warning");
  });
})();

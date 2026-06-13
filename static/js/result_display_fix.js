(function () {
  'use strict';

  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  function findPredictionCard() {
    const headings = qsa('h1,h2,h3,h4,.card-title,.section-title');
    for (const h of headings) {
      if ((h.textContent || '').trim().toLowerCase().includes('prediction result')) {
        return h.closest('.card, .panel, section, .dashboard-card, .result-card, .content-card') || h.parentElement;
      }
    }
    return qs('#predictionResult') || qs('#resultPanel') || qs('.prediction-result') || qs('.result-card');
  }

  function ensureResultBody() {
    const card = findPredictionCard();
    if (!card) return null;
    let body = qs('#prediction-result-body', card);
    if (!body) {
      body = document.createElement('div');
      body.id = 'prediction-result-body';
      body.className = 'prediction-result-body';
      const heading = qsa('h1,h2,h3,h4,.card-title,.section-title', card).find(h => (h.textContent || '').toLowerCase().includes('prediction result'));
      if (heading) {
        heading.insertAdjacentElement('afterend', body);
      } else {
        card.appendChild(body);
      }
    }
    return body;
  }

  function emptyResult() {
    const body = ensureResultBody();
    if (!body) return;
    body.innerHTML = `
      <div class="result-empty-state">
        <div class="result-empty-icon">🍃</div>
        <h3>Prediction result will appear here after analysis.</h3>
        <p>Upload or capture a walnut leaf image and click Analyze Leaf.</p>
      </div>
    `;
  }

  function showLoading() {
    const body = ensureResultBody();
    if (!body) return;
    body.innerHTML = `
      <div class="result-loading-state">
        <div class="result-spinner"></div>
        <h3>Analyzing leaf image...</h3>
        <p>Please wait while the model processes the image.</p>
      </div>
    `;
  }

  function showError(message, imageUrl) {
    const body = ensureResultBody();
    if (!body) return;
    const img = imageUrl ? `<div class="result-image-wrap"><img src="${escapeAttr(imageUrl)}" alt="Uploaded image"></div>` : '';
    body.innerHTML = `
      <div class="result-warning-box">
        <div class="warning-icon">!</div>
        <div>
          <h3>Image Warning</h3>
          <p>${escapeHtml(message || 'Unable to analyze this image. Please upload a clear walnut leaf image.')}</p>
        </div>
      </div>
      ${img}
    `;
  }

  function showSuccess(data) {
    const body = ensureResultBody();
    if (!body) return;
    const confidence = Number(data.confidence || 0).toFixed(2);
    const predicted = data.predicted_class_display || data.predicted_class || 'Unknown';
    const recommendation = data.recommendation || '';
    const imageUrl = data.image_url || '';
    const download = data.history_id ? `<a class="pretty-btn pretty-btn-outline" href="/download-result/${encodeURIComponent(data.history_id)}">Download Result</a>` : '';

    body.innerHTML = `
      ${imageUrl ? `<div class="result-image-wrap"><img src="${escapeAttr(imageUrl)}" alt="Uploaded walnut leaf"></div>` : ''}
      <div class="result-summary-card">
        <div class="result-label">Predicted Class</div>
        <div class="result-class">${escapeHtml(predicted)}</div>
        <div class="result-label">Confidence Score</div>
        <div class="result-confidence">${confidence}%</div>
        <div class="confidence-bar"><span style="width:${Math.max(0, Math.min(100, confidence))}%"></span></div>
      </div>
      <div class="result-recommendation-card">
        <h3>Treatment Recommendation</h3>
        <p>${escapeHtml(recommendation)}</p>
      </div>
      <div class="result-actions">
        ${download}
      </div>
    `;
  }

  function escapeHtml(str) {
    return String(str).replace(/[&<>'"]/g, function (ch) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[ch];
    });
  }

  function escapeAttr(str) { return escapeHtml(str); }

  function findImageInput() {
    return qs('input[type="file"][name="image"]') || qs('input[type="file"]#imageInput') || qs('input[type="file"]#fileInput') || qs('input[type="file"]');
  }

  function findAnalyzeButton() {
    const candidates = qsa('button, input[type="submit"], a');
    return candidates.find(el => (el.textContent || el.value || '').trim().toLowerCase().includes('analyze leaf')) || qs('#analyzeBtn') || qs('#analyzeButton');
  }

  function getFormData() {
    const input = findImageInput();
    if (!input || !input.files || !input.files[0]) {
      showError('Please upload a walnut leaf image before analysis.');
      return null;
    }
    const fd = new FormData();
    fd.append('image', input.files[0]);
    return fd;
  }

  async function runPrediction(evt) {
    if (evt) {
      evt.preventDefault();
      evt.stopPropagation();
    }

    const fd = getFormData();
    if (!fd) return false;

    const btn = findAnalyzeButton();
    const oldText = btn ? (btn.textContent || btn.value) : '';
    if (btn) {
      btn.disabled = true;
      if ('value' in btn) btn.value = 'Analyzing image...';
      btn.textContent = 'Analyzing image...';
    }

    showLoading();

    try {
      const response = await fetch('/predict', { method: 'POST', body: fd });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || data.success === false) {
        showError(data.error || 'Prediction failed. Please try another clear walnut leaf image.', data.image_url);
      } else {
        showSuccess(data);
      }
    } catch (err) {
      showError('Could not connect to the prediction server. Please restart Flask and try again.');
    } finally {
      if (btn) {
        btn.disabled = false;
        if ('value' in btn) btn.value = oldText || 'Analyze Leaf';
        btn.textContent = oldText || 'Analyze Leaf';
      }
    }

    return false;
  }

  function bindEvents() {
    const input = findImageInput();
    if (input && !input.dataset.resultFixBound) {
      input.dataset.resultFixBound = '1';
      input.addEventListener('change', emptyResult);
    }

    const analyzeBtn = findAnalyzeButton();
    if (analyzeBtn && !analyzeBtn.dataset.resultFixBound) {
      analyzeBtn.dataset.resultFixBound = '1';
      analyzeBtn.addEventListener('click', runPrediction, true);
    }

    const form = analyzeBtn ? analyzeBtn.closest('form') : qs('form');
    if (form && !form.dataset.resultFixBound) {
      form.dataset.resultFixBound = '1';
      form.addEventListener('submit', runPrediction, true);
    }

    qsa('[data-action="remove-image"], .remove-image, #removeImage, #removeImageBtn, button').forEach(btn => {
      const txt = (btn.textContent || '').trim().toLowerCase();
      if (txt.includes('remove image') && !btn.dataset.resultFixRemoveBound) {
        btn.dataset.resultFixRemoveBound = '1';
        btn.addEventListener('click', emptyResult);
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    bindEvents();
    if (!ensureResultBody().innerHTML.trim()) emptyResult();
    const mo = new MutationObserver(bindEvents);
    mo.observe(document.body, { childList: true, subtree: true });
  });
})();

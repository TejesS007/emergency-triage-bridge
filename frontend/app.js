/**
 * Emergency Triage Bridge - Frontend Application Logic
 * Mobile-first, accessible, zero animations, pure Vanilla JavaScript.
 */

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("triage-form");
  const photoInput = document.getElementById("photo-input");
  const fileInfo = document.getElementById("file-info");
  const symptomInput = document.getElementById("symptom-input");
  const analyzeButton = document.getElementById("analyze-button");
  const resetButton = document.getElementById("reset-button");
  const statusMessage = document.getElementById("status-message");

  const resultsSection = document.getElementById("results-section");
  const resultSeverity = document.getElementById("result-severity");
  const resultCondition = document.getElementById("result-condition");
  const resultAction = document.getElementById("result-action");
  const resultMedications = document.getElementById("result-medications");
  const resultAllergies = document.getElementById("result-allergies");
  const hospitalName = document.getElementById("hospital-name");
  const hospitalDistance = document.getElementById("hospital-distance");
  const hospitalAddressWrapper = document.getElementById("hospital-address-wrapper");
  const hospitalAddress = document.getElementById("hospital-address");
  const shareableText = document.getElementById("shareable-text");
  const copySummaryButton = document.getElementById("copy-summary-button");
  const copyConfirmation = document.getElementById("copy-confirmation");

  const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
  const ALLOWED_TYPES = ["image/jpeg", "image/png"];

  // Display selected file info and validate upfront
  photoInput.addEventListener("change", () => {
    const file = photoInput.files[0];
    if (file) {
      if (!ALLOWED_TYPES.includes(file.type)) {
        showStatus(`Invalid file format '${file.type}'. Only JPEG and PNG are allowed.`, "error");
        photoInput.value = "";
        fileInfo.textContent = "";
        return;
      }
      if (file.size > MAX_FILE_SIZE) {
        showStatus(`File is too large (${(file.size / (1024 * 1024)).toFixed(2)} MB). Max limit is 5MB.`, "error");
        photoInput.value = "";
        fileInfo.textContent = "";
        return;
      }
      hideStatus();
      fileInfo.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    } else {
      fileInfo.textContent = "";
    }
  });

  // Handle form submission
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    hideStatus();
    copyConfirmation.textContent = "";

    const file = photoInput.files[0];
    const text = symptomInput.value.trim();

    if (!file && !text) {
      showStatus("Please upload a photo or enter a symptom description before analyzing.", "error");
      return;
    }

    if (file && !ALLOWED_TYPES.includes(file.type)) {
      showStatus("Invalid file type. Only JPEG and PNG images are supported.", "error");
      return;
    }

    if (file && file.size > MAX_FILE_SIZE) {
      showStatus("File size exceeds 5MB limit.", "error");
      return;
    }

    // Prepare multipart form data
    const formData = new FormData();
    if (file) {
      formData.append("file", file);
    }
    if (text) {
      formData.append("text", text);
    }

    setLoading(true);

    try {
      const response = await fetch("/analyze", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const message = errorData.detail || `Server error (${response.status})`;
        throw new Error(message);
      }

      const data = await response.json();
      renderResults(data);
    } catch (error) {
      console.error("Triage analysis error:", error);
      showStatus(`Analysis failed: ${error.message}`, "error");
      resultsSection.hidden = true;
    } finally {
      setLoading(false);
    }
  });

  // Render triage results
  function renderResults(data) {
    resultsSection.classList.remove("hidden");
    resultsSection.style.display = "";
    const severity = (data.severity || "medium").toLowerCase();
    resultSeverity.textContent = severity.toUpperCase();
    resultSeverity.className = `severity-badge severity-${severity}`;

    resultCondition.textContent = data.condition_summary || "No condition summary provided.";
    resultAction.textContent = data.recommended_action || "Consult healthcare provider.";

    // Render Medications
    resultMedications.innerHTML = "";
    if (Array.isArray(data.medications) && data.medications.length > 0) {
      data.medications.forEach((med) => {
        const li = document.createElement("li");
        li.textContent = med;
        resultMedications.appendChild(li);
      });
    } else {
      const li = document.createElement("li");
      li.textContent = "None reported";
      resultMedications.appendChild(li);
    }

    // Render Allergies
    resultAllergies.innerHTML = "";
    if (Array.isArray(data.allergies) && data.allergies.length > 0) {
      data.allergies.forEach((allergy) => {
        const li = document.createElement("li");
        li.textContent = allergy;
        resultAllergies.appendChild(li);
      });
    } else {
      const li = document.createElement("li");
      li.textContent = "None reported";
      resultAllergies.appendChild(li);
    }

    // Hospital info
    if (data.nearest_hospital) {
      hospitalName.textContent = data.nearest_hospital.name || "Emergency Medical Facility";
      hospitalDistance.textContent = `${data.nearest_hospital.distance_km.toFixed(2)} km away`;
      if (data.nearest_hospital.address) {
        hospitalAddress.textContent = data.nearest_hospital.address;
        hospitalAddressWrapper.hidden = false;
      } else {
        hospitalAddressWrapper.hidden = true;
      }
    }

    // Shareable summary
    shareableText.value = data.shareable_summary || "";

    resultsSection.hidden = false;
    resultsSection.scrollIntoView({ behavior: "auto", block: "start" });
  }

  // Copy shareable summary to clipboard
  copySummaryButton.addEventListener("click", async () => {
    if (!shareableText.value) return;

    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(shareableText.value);
      } else {
        // Fallback for older browsers
        shareableText.select();
        document.execCommand("copy");
      }
      copyConfirmation.textContent = "✓ Copied to clipboard!";
      setTimeout(() => {
        copyConfirmation.textContent = "";
      }, 4000);
    } catch (err) {
      console.error("Clipboard copy failed:", err);
      copyConfirmation.textContent = "Selection copied manually.";
    }
  });

  // Reset form and UI state
  // Reset form and UI state
  resetButton.addEventListener("click", () => {
    form.reset();
    fileInfo.textContent = "";
    hideStatus();
    resultsSection.hidden = true;
    copyConfirmation.textContent = "";
  });

  function showStatus(message, type = "info") {
    statusMessage.textContent = message;
    statusMessage.className = `status-banner ${type}`;
    statusMessage.hidden = false;
  }

  function hideStatus() {
    statusMessage.hidden = true;
    statusMessage.textContent = "";
  }

  function setLoading(isLoading) {
    if (isLoading) {
      analyzeButton.disabled = true;
      analyzeButton.textContent = "Analyzing Emergency Case...";
      showStatus("Evaluating triage case with clinical AI...", "info");
    } else {
      analyzeButton.disabled = false;
      analyzeButton.textContent = "Analyze Emergency Case";
      if (statusMessage.classList.contains("info")) {
        hideStatus();
      }
    }
  }
});

# Emergency Triage Bridge

Emergency Triage Bridge is a mobile-first, high-accessibility web application designed for rapid emergency patient intake and triage assessment. Powered by Google Gemini 3.6 Flash, the system analyzes patient trauma photos or symptom descriptions to categorize clinical severity and extract vital clinical data. It automatically connects with the Google Places API to route patients to the nearest medical facility while generating a standardized shareable summary for first responders.

---

## Setup Instructions

### 1. Prerequisites
- Python 3.11+
- Virtual environment tool (`venv`)
- (Optional) Docker for containerized execution

### 2. Environment Variables
Create a `.env` file or export the following API keys in your terminal:

```bash
export GEMINI_API_KEY="your-gemini-api-key"
export GOOGLE_PLACES_API_KEY="your-google-places-api-key"
```

> **Note:** The application includes fault-tolerant fallbacks if API keys are not provided or if external services encounter temporary issues.

### 3. Install Dependencies
```bash
python -m venv venv
# On Linux/macOS:
source venv/bin/activate
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

---

## How to Run Locally

### Start Development Server
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser and navigate to:
```
http://localhost:8000
```

### Run Automated Tests
```bash
pytest -v
```

---

## Running with Docker / Cloud Run

### Build and Run Docker Image
```bash
docker build -t emergency-triage-bridge .
docker run -p 8080:8080 -e GEMINI_API_KEY="your-key" -e GOOGLE_PLACES_API_KEY="your-key" emergency-triage-bridge
```

### Deploy to Google Cloud Run
```bash
gcloud run deploy emergency-triage-bridge \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY="your-key",GOOGLE_PLACES_API_KEY="your-key"
```

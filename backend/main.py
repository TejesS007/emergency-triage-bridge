import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.gemini_client import analyze_triage
from backend.places_client import get_nearest_hospital
from backend.schema import AnalyzeResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("emergency_triage_bridge")

app = FastAPI(
    title="Emergency Triage Bridge",
    description="Multimodal emergency triage assistant and hospital routing API",
    version="1.0.0",
)

# Enable CORS for development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE = 4 * 1024 * 1024  # 4 MB
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png"}


def build_shareable_summary(
    severity: str,
    condition_summary: str,
    recommended_action: str,
    medications: list,
    allergies: list,
    hospital_name: str,
    hospital_distance_km: float,
) -> str:
    """Constructs a concise, formatted text summary for sharing via local f-string."""
    meds_str = ", ".join(medications) if medications else "None reported"
    allergies_str = ", ".join(allergies) if allergies else "None reported"
    return (
        f"[EMERGENCY TRIAGE SUMMARY]\n"
        f"SEVERITY: {severity.upper()}\n"
        f"CONDITION: {condition_summary}\n"
        f"RECOMMENDED ACTION: {recommended_action}\n"
        f"MEDICATIONS: {meds_str}\n"
        f"ALLERGIES: {allergies_str}\n"
        f"NEAREST FACILITY: {hospital_name} ({hospital_distance_km:.2f} km)"
    )


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_emergency(
    file: Optional[UploadFile] = File(default=None),
    text: Optional[str] = Form(default=None),
    lat: Optional[float] = Form(default=None),
    lng: Optional[float] = Form(default=None),
) -> AnalyzeResponse:
    """
    Accepts an image file (JPEG/PNG, <=5MB) or text description,
    performs AI triage analysis and locates the nearest hospital.
    """
    image_bytes: Optional[bytes] = None
    mime_type: Optional[str] = None

    if file and file.filename:
        content_type = file.content_type or ""
        if content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type '{content_type}'. Only image/jpeg and image/png are supported.",
            )

        image_bytes = await file.read()
        if len(image_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size of {len(image_bytes)} bytes exceeds the maximum 5MB limit.",
            )
        mime_type = content_type

    cleaned_text = text.strip() if text else None
    if not image_bytes and not cleaned_text:
        raise HTTPException(
            status_code=400,
            detail="Missing input: please provide an image file or a symptom description.",
        )

    triage = analyze_triage(
        image_bytes=image_bytes,
        mime_type=mime_type,
        text=cleaned_text,
    )

    if lat is not None and lng is not None:
        hospital = get_nearest_hospital(lat, lng)
    else:
        hospital = get_nearest_hospital()

    shareable = build_shareable_summary(
        severity=triage.severity,
        condition_summary=triage.condition_summary,
        recommended_action=triage.recommended_action,
        medications=triage.medications,
        allergies=triage.allergies,
        hospital_name=hospital.name,
        hospital_distance_km=hospital.distance_km,
    )

    return AnalyzeResponse(
        severity=triage.severity,
        condition_summary=triage.condition_summary,
        medications=triage.medications,
        allergies=triage.allergies,
        recommended_action=triage.recommended_action,
        nearest_hospital=hospital,
        shareable_summary=shareable,
    )


frontend_dir = Path(__file__).resolve().parent.parent / "frontend"

if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    async def serve_index():
        index_file = frontend_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Emergency Triage Bridge API is active. Frontend index.html not found."}
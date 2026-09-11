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
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class TriageAssessment(BaseModel):
    """Pydantic model representing structured clinical triage assessment output."""
    severity: Literal["low", "medium", "high", "critical"] = Field(
        description="Assessed emergency severity level: low, medium, high, or critical."
    )
    condition_summary: str = Field(
        description="Concise clinical summary of the patient's symptoms or physical condition."
    )
    medications: List[str] = Field(
        default_factory=list,
        description="List of detected or stated medications relevant to the patient."
    )
    allergies: List[str] = Field(
        default_factory=list,
        description="List of detected or stated patient allergies."
    )
    recommended_action: str = Field(
        description="Clear, immediate clinical or first-aid recommendation."
    )


class NearestHospital(BaseModel):
    """Information about the nearest medical facility."""
    name: str = Field(description="Name of the hospital or medical center.")
    distance_km: float = Field(description="Distance in kilometers from patient location.")
    address: Optional[str] = Field(default=None, description="Formatted address of the hospital.")


class AnalyzeResponse(BaseModel):
    """Combined response model returned by POST /analyze."""
    severity: Literal["low", "medium", "high", "critical"]
    condition_summary: str
    medications: List[str]
    allergies: List[str]
    recommended_action: str
    nearest_hospital: NearestHospital
    shareable_summary: str

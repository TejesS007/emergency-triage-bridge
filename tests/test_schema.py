import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.gemini_client import FALLBACK_ASSESSMENT
from backend.main import app
from backend.schema import AnalyzeResponse, NearestHospital, TriageAssessment


# ==========================================
# Unit Tests for Pydantic Schema
# ==========================================

def test_valid_input_passes_validation():
    """Test that all valid severity levels and properly formed data pass validation."""
    valid_severities = ["low", "medium", "high", "critical"]
    for sev in valid_severities:
        assessment = TriageAssessment(
            severity=sev,
            condition_summary="Patient exhibits mild abrasion on left forearm.",
            medications=["Ibuprofen 200mg"],
            allergies=["Penicillin"],
            recommended_action="Clean wound and apply sterile dressing.",
        )
        assert assessment.severity == sev
        assert assessment.condition_summary == "Patient exhibits mild abrasion on left forearm."
        assert len(assessment.medications) == 1
        assert len(assessment.allergies) == 1


def test_missing_required_field_raises_validation_error():
    """Test that omitting required fields raises a Pydantic ValidationError."""
    # Missing condition_summary
    with pytest.raises(ValidationError) as exc_info:
        TriageAssessment.model_validate({
            "severity": "high",
            "medications": [],
            "allergies": [],
            "recommended_action": "Administer oxygen.",
        })
    errors = exc_info.value.errors()
    assert any(err["loc"] == ("condition_summary",) for err in errors)

    # Missing severity
    with pytest.raises(ValidationError) as exc_info:
        TriageAssessment.model_validate({
            "condition_summary": "Severe shortness of breath",
            "medications": [],
            "allergies": [],
            "recommended_action": "Emergency transport",
        })
    errors = exc_info.value.errors()
    assert any(err["loc"] == ("severity",) for err in errors)


def test_invalid_severity_value_raises_validation_error():
    """Test that invalid severity values outside {'low', 'medium', 'high', 'critical'} raise ValidationError."""
    invalid_values = ["urgent", "moderate", "severe", "extreme", "unknown", 123]
    for invalid_sev in invalid_values:
        with pytest.raises(ValidationError) as exc_info:
            TriageAssessment.model_validate({
                "severity": invalid_sev,
                "condition_summary": "Chest pain radiating to left shoulder.",
                "medications": [],
                "allergies": [],
                "recommended_action": "Call 911 immediately.",
            })
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("severity",) for err in errors)


def test_fallback_assessment_is_valid_schema():
    """Test that the hardcoded fallback object strictly adheres to the schema."""
    assert isinstance(FALLBACK_ASSESSMENT, TriageAssessment)
    assert FALLBACK_ASSESSMENT.severity == "medium"
    assert FALLBACK_ASSESSMENT.condition_summary == "Unable to analyze — manual review needed"
    assert FALLBACK_ASSESSMENT.medications == []
    assert FALLBACK_ASSESSMENT.allergies == []
    assert FALLBACK_ASSESSMENT.recommended_action == "Consult a medical professional immediately"


# ==========================================
# Integration Tests using FastAPI TestClient
# ==========================================

def test_analyze_endpoint_with_text_only_input():
    """
    Integration test: POSTs to /analyze with text-only input and asserts 200 response
    with all expected JSON keys present.
    """
    client = TestClient(app)
    response = client.post("/analyze", data={"text": "Patient has severe headache and dizziness for 2 hours."})

    assert response.status_code == 200
    data = response.json()

    # Validate that all expected keys are present
    expected_keys = {
        "severity",
        "condition_summary",
        "medications",
        "allergies",
        "recommended_action",
        "nearest_hospital",
        "shareable_summary",
    }
    assert expected_keys.issubset(data.keys())

    # Validate severity is one of the four allowed values
    assert data["severity"] in ["low", "medium", "high", "critical"]

    # Validate nearest_hospital structure
    assert "name" in data["nearest_hospital"]
    assert "distance_km" in data["nearest_hospital"]
    assert isinstance(data["nearest_hospital"]["distance_km"], (int, float))

    # Validate shareable summary is a non-empty string
    assert isinstance(data["shareable_summary"], str)
    assert len(data["shareable_summary"]) > 0


def test_analyze_endpoint_invalid_file_type():
    """Test that uploading a disallowed file type returns 400 Bad Request."""
    client = TestClient(app)
    fake_txt_file = ("test.txt", b"This is plain text not an image", "text/plain")
    response = client.post("/analyze", files={"file": fake_txt_file})

    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_analyze_endpoint_oversized_file():
    """Test that uploading a file > 5MB returns 400 Bad Request."""
    client = TestClient(app)
    # 5.1 MB dummy content
    oversized_data = b"0" * (5 * 1024 * 1024 + 1024)
    fake_big_img = ("large.png", oversized_data, "image/png")
    response = client.post("/analyze", files={"file": fake_big_img})

    assert response.status_code == 400
    assert "exceeds the maximum 5MB limit" in response.json()["detail"]


def test_analyze_endpoint_no_input_returns_400():
    """Test that sending an empty request returns 400."""
    client = TestClient(app)
    response = client.post("/analyze", data={})
    assert response.status_code == 400
    assert "Missing input" in response.json()["detail"]

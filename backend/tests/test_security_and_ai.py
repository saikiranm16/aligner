from pathlib import Path

from fastapi import HTTPException

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.services.document_intelligence import DocumentIntelligenceService
from app.services.file_validation import SecureUploadValidator


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("StrongPass123")
    assert verify_password("StrongPass123", hashed) is True
    assert verify_password("WrongPass123", hashed) is False


def test_access_token_roundtrip() -> None:
    token = create_access_token(7, "qa@example.com")
    payload = decode_access_token(token)
    assert payload["sub"] == 7
    assert payload["email"] == "qa@example.com"


def test_file_validator_rejects_non_pdf_signature(tmp_path: Path) -> None:
    validator = SecureUploadValidator()
    file_path = tmp_path / "bad.pdf"
    file_path.write_bytes(b"NOT_A_REAL_PDF")

    try:
        validator.validate_pdf(file_path)
        assert False, "Expected validation to fail for an invalid PDF signature."
    except HTTPException as exc:
        assert exc.detail == "The uploaded file is not a valid PDF."


def test_document_intelligence_extractive_summary() -> None:
    service = DocumentIntelligenceService()
    text = (
        "AlignPDF converts complex documents into editable Word files. "
        "It preserves formatting, tables, and page structure. "
        "The system also generates document summaries and insights."
    )
    summary = service.summarize(
        job_id="job123",
        source_type="pdf",
        text=text,
        mode="extractive",
        length="short",
        language_hint="en",
    )
    assert "AlignPDF converts complex documents" in summary.summary_text
    assert summary.model_used == "heuristic-extractive-ranker"

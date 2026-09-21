import os
import mimetypes

from django.core.exceptions import ValidationError
from .file_signatures import detect_file_type


MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


ALLOWED_FILE_TYPES = {
    ".pdf": {
        "mime_types": [
            "application/pdf",
        ],
        "expected_signature": "application/pdf",
    },
    ".doc": {
        "mime_types": [
            "application/msword",
        ],
        "expected_signature": "application/ms-office",
    },
    ".docx": {
        "mime_types": [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ],
        "expected_signature": "application/zip",
    },
    ".ppt": {
        "mime_types": [
            "application/vnd.ms-powerpoint",
        ],
        "expected_signature": "application/ms-office",
    },
    ".pptx": {
        "mime_types": [
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ],
        "expected_signature": "application/zip",
    },
    ".xls": {
        "mime_types": [
            "application/vnd.ms-excel",
        ],
        "expected_signature": "application/ms-office",
    },
    ".xlsx": {
        "mime_types": [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ],
        "expected_signature": "application/zip",
    },
    ".txt": {
        "mime_types": [
            "text/plain",
        ],
        "expected_signature": None,
    },
}


def validate_study_material_file(uploaded_file):
    """
    Validate uploaded study material.

    Checks:
    - file exists
    - extension
    - file size
    - MIME type
    - file signature
    """

    if not uploaded_file:
        raise ValidationError("No file was uploaded.")

    filename = uploaded_file.name or ""

    extension = os.path.splitext(filename)[1].lower()

    if extension not in ALLOWED_FILE_TYPES:
        raise ValidationError(
            "Unsupported file type. "
            "Allowed: PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX and TXT."
        )

    if uploaded_file.size > MAX_FILE_SIZE:
        raise ValidationError(
            "File size cannot exceed 20 MB."
        )

    detected_mime, _ = mimetypes.guess_type(filename)

    allowed_mimes = ALLOWED_FILE_TYPES[extension]["mime_types"]

    # Some browsers may not provide a reliable content_type,
    # so use the uploaded content type first and filename MIME
    # as a secondary check.
    uploaded_mime = getattr(uploaded_file, "content_type", None)

    if uploaded_mime and uploaded_mime not in allowed_mimes:
        raise ValidationError(
            f"Invalid MIME type: {uploaded_mime}"
        )

    if detected_mime and detected_mime not in allowed_mimes:
        raise ValidationError(
            "File extension does not match its expected MIME type."
        )

    # Signature validation where practical
    expected_sig = ALLOWED_FILE_TYPES[extension].get("expected_signature")
    if expected_sig:
        detected_sig = detect_file_type(uploaded_file)
        if detected_sig != expected_sig:
            raise ValidationError(
                "File content does not match its file extension signature."
            )

    return True


PREVIOUS_YEAR_PAPER_ALLOWED_EXTENSIONS = {
    ".pdf": [
        "application/pdf",
    ],
}


def validate_previous_year_paper_file(uploaded_file):
    if not uploaded_file:
        raise ValidationError(
            "A paper file is required."
        )

    filename = uploaded_file.name or ""

    extension = os.path.splitext(filename)[1].lower()

    if extension not in PREVIOUS_YEAR_PAPER_ALLOWED_EXTENSIONS:
        raise ValidationError(
            "Only PDF files are allowed."
        )

    max_size = 20 * 1024 * 1024

    if uploaded_file.size > max_size:
        raise ValidationError(
            "File size cannot exceed 20 MB."
        )

    content_type = getattr(
        uploaded_file,
        "content_type",
        ""
    )

    if content_type and content_type != "application/pdf":
        raise ValidationError(
            "The uploaded file must be a PDF."
        )

    detected_sig = detect_file_type(uploaded_file)
    if detected_sig and detected_sig != "application/pdf":
        raise ValidationError(
            "File content does not match PDF signature."
        )

    return uploaded_file

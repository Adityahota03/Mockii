from django.core.exceptions import ValidationError


def detect_file_signature(uploaded_file):
    uploaded_file.seek(0)
    header = uploaded_file.read(16)
    uploaded_file.seek(0)

    if header.startswith(b"%PDF"):
        return "application/pdf"

    if header.startswith(b"\xD0\xCF\x11\xE0"):
        return "application/ms-office"

    if header.startswith(b"PK"):
        return "application/zip"

    if header.startswith(b"\xFF\xFE") or header.startswith(b"\xFE\xFF"):
        return "text/plain"

    return None


detect_file_type = detect_file_signature


def validate_pdf_signature(uploaded_file):
    detected_type = detect_file_signature(uploaded_file)
    if detected_type != "application/pdf":
        raise ValidationError("The uploaded file is not a valid PDF.")


def validate_study_material_signature(uploaded_file, extension):
    detected_type = detect_file_signature(uploaded_file)

    if extension == ".pdf":
        if detected_type != "application/pdf":
            raise ValidationError("Invalid PDF file signature.")
    elif extension in {".docx", ".pptx", ".xlsx"}:
        if detected_type != "application/zip":
            raise ValidationError("Invalid Office file signature.")
    elif extension in {".doc", ".xls", ".ppt"}:
        if detected_type != "application/ms-office":
            raise ValidationError("Invalid Office file signature.")

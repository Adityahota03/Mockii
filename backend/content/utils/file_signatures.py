def detect_file_type(uploaded_file):
    uploaded_file.seek(0)
    header = uploaded_file.read(16)
    uploaded_file.seek(0)

    if header.startswith(b"%PDF"):
        return "application/pdf"

    if header.startswith(b"PK"):
        # DOCX / PPTX / XLSX are ZIP-based Office files.
        return "application/zip"

    if header.startswith(b"\xD0\xCF\x11\xE0"):
        # Old Microsoft Office formats.
        return "application/ms-office"

    return None

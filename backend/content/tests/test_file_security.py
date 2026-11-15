import os
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from content.models import ExamCategory, Exam, StudyMaterial, PreviousYearPaper
from content.serializers import AdminStudyMaterialSerializer

User = get_user_model()


class FileUploadDownloadSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.password = "StrongPass123!"

        self.student = User.objects.create_user(
            email="student_file@example.com",
            password=self.password,
            role="STUDENT",
        )
        self.admin = User.objects.create_user(
            email="admin_file@example.com",
            password=self.password,
            role="ADMIN",
        )

        self.category = ExamCategory.objects.create(
            name="Defense",
            slug="defense",
            is_active=True,
        )
        self.exam = Exam.objects.create(
            category=self.category,
            name="NDA Exam",
            slug="nda-exam",
            is_active=True,
        )

        # Minimal valid PDF bytes
        self.valid_pdf_content = (
            b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
            b"2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n"
            b"3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\n"
            b"xref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \n"
            b"trailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n190\n%%EOF"
        )

    def tearDown(self):
        for m in StudyMaterial.objects.all():
            try:
                if m.file:
                    m.file.close()
                    if m.file.storage.exists(m.file.name):
                        m.file.storage.delete(m.file.name)
            except Exception:
                pass
        for p in PreviousYearPaper.objects.all():
            try:
                if p.file:
                    p.file.close()
                    if p.file.storage.exists(p.file.name):
                        p.file.storage.delete(p.file.name)
            except Exception:
                pass

    # -------------------------------------------------------------
    # STUDY MATERIAL UPLOAD VALIDATION & SECURITY
    # -------------------------------------------------------------
    def test_admin_uploads_valid_pdf_succeeds(self):
        self.client.force_authenticate(user=self.admin)
        uploaded = SimpleUploadedFile(
            "physics_notes.pdf",
            self.valid_pdf_content,
            content_type="application/pdf",
        )
        res = self.client.post(
            "/api/content/admin/study-materials/",
            {
                "exam": self.exam.id,
                "title": "Physics Notes",
                "category": "Notes",
                "material_type": "PDF",
                "file": uploaded,
            },
            format="multipart",
        )
        self.assertEqual(res.status_code, 201)
        material = StudyMaterial.objects.get(id=res.data["id"])
        self.assertTrue(material.file.name.startswith("study_materials/exam_"))
        self.assertTrue(material.file.name.endswith(".pdf"))
        # Verify stored name uses UUID, not original physics_notes.pdf
        filename_part = os.path.basename(material.file.name)
        self.assertNotIn("physics_notes", filename_part)

    def test_study_material_rejects_fake_pdf(self):
        self.client.force_authenticate(user=self.admin)
        # Executable/text content renamed to .pdf
        fake_pdf = SimpleUploadedFile(
            "malware.pdf",
            b"MZ\x90\x00\x03\x00\x00\x00FakePEHeaderBytesHere",
            content_type="application/pdf",
        )
        res = self.client.post(
            "/api/content/admin/study-materials/",
            {
                "exam": self.exam.id,
                "title": "Fake PDF",
                "category": "Notes",
                "material_type": "PDF",
                "file": fake_pdf,
            },
            format="multipart",
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("file", res.data)

    def test_study_material_rejects_executable_files(self):
        self.client.force_authenticate(user=self.admin)
        exe_file = SimpleUploadedFile(
            "virus.exe",
            b"MZ\x90\x00\x03\x00\x00\x00ExecutableContent",
            content_type="application/x-msdownload",
        )
        res = self.client.post(
            "/api/content/admin/study-materials/",
            {
                "exam": self.exam.id,
                "title": "Executable Attempt",
                "category": "Notes",
                "material_type": "PDF",
                "file": exe_file,
            },
            format="multipart",
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("file", res.data)

    def test_study_material_rejects_dangerous_web_extensions(self):
        self.client.force_authenticate(user=self.admin)
        html_file = SimpleUploadedFile(
            "exploit.html",
            b"<script>alert(1)</script>",
            content_type="text/html",
        )
        res = self.client.post(
            "/api/content/admin/study-materials/",
            {
                "exam": self.exam.id,
                "title": "HTML Exploit",
                "category": "Notes",
                "material_type": "TXT",
                "file": html_file,
            },
            format="multipart",
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("file", res.data)

    def test_study_material_rejects_empty_file(self):
        self.client.force_authenticate(user=self.admin)
        empty_file = SimpleUploadedFile(
            "empty.pdf",
            b"",
            content_type="application/pdf",
        )
        res = self.client.post(
            "/api/content/admin/study-materials/",
            {
                "exam": self.exam.id,
                "title": "Empty File",
                "category": "Notes",
                "material_type": "PDF",
                "file": empty_file,
            },
            format="multipart",
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("file", res.data)

    def test_study_material_rejects_oversized_file(self):
        oversized = SimpleUploadedFile(
            "large.pdf",
            self.valid_pdf_content,
            content_type="application/pdf",
        )
        oversized.size = 21 * 1024 * 1024

        serializer = AdminStudyMaterialSerializer(
            data={
                "exam": self.exam.id,
                "title": "Large File",
                "category": "Notes",
                "material_type": "PDF",
                "file": oversized,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("file", serializer.errors)

    def test_path_traversal_filename_is_neutralized(self):
        self.client.force_authenticate(user=self.admin)
        traversal_file = SimpleUploadedFile(
            "../../etc/passwd.pdf",
            self.valid_pdf_content,
            content_type="application/pdf",
        )
        res = self.client.post(
            "/api/content/admin/study-materials/",
            {
                "exam": self.exam.id,
                "title": "Traversal Attempt",
                "category": "Notes",
                "material_type": "PDF",
                "file": traversal_file,
            },
            format="multipart",
        )
        self.assertEqual(res.status_code, 201)
        material = StudyMaterial.objects.get(id=res.data["id"])
        self.assertNotIn("..", material.file.name)
        self.assertNotIn("passwd", material.file.name)
        self.assertTrue(material.file.name.startswith("study_materials/exam_"))

    # -------------------------------------------------------------
    # PREVIOUS YEAR PAPER UPLOAD VALIDATION & SECURITY
    # -------------------------------------------------------------
    def test_previous_year_paper_rejects_non_pdf_and_fake_pdf(self):
        self.client.force_authenticate(user=self.admin)

        # Word document renamed to .pdf
        fake_word_pdf = SimpleUploadedFile(
            "paper.pdf",
            b"\xD0\xCF\x11\xE0OldWordDocBytesHere",
            content_type="application/pdf",
        )
        res1 = self.client.post(
            "/api/content/admin/previous-year-papers/",
            {
                "exam": self.exam.id,
                "title": "PYQ 2021",
                "year": 2021,
                "file": fake_word_pdf,
            },
            format="multipart",
        )
        self.assertEqual(res1.status_code, 400)
        self.assertIn("file", res1.data)

        # ZIP archive renamed to .pdf
        fake_zip_pdf = SimpleUploadedFile(
            "paper2.pdf",
            b"PK\x03\x04ZipArchiveBytesHere",
            content_type="application/pdf",
        )
        res2 = self.client.post(
            "/api/content/admin/previous-year-papers/",
            {
                "exam": self.exam.id,
                "title": "PYQ 2022",
                "year": 2022,
                "file": fake_zip_pdf,
            },
            format="multipart",
        )
        self.assertEqual(res2.status_code, 400)
        self.assertIn("file", res2.data)

    # -------------------------------------------------------------
    # UPLOAD & DELETION AUTHORIZATION
    # -------------------------------------------------------------
    def test_student_and_anonymous_cannot_upload_or_delete(self):
        uploaded = SimpleUploadedFile(
            "student_notes.pdf",
            self.valid_pdf_content,
            content_type="application/pdf",
        )

        # Anonymous upload -> 401
        anon_res = self.client.post(
            "/api/content/admin/study-materials/",
            {"exam": self.exam.id, "title": "Test", "material_type": "PDF", "file": uploaded},
            format="multipart",
        )
        self.assertEqual(anon_res.status_code, 401)

        # Student upload -> 403
        self.client.force_authenticate(user=self.student)
        student_res = self.client.post(
            "/api/content/admin/study-materials/",
            {"exam": self.exam.id, "title": "Test", "material_type": "PDF", "file": uploaded},
            format="multipart",
        )
        self.assertEqual(student_res.status_code, 403)

        # Student delete -> 403
        material = StudyMaterial.objects.create(
            exam=self.exam,
            title="Admin Material",
            material_type="PDF",
            file=SimpleUploadedFile("orig.pdf", self.valid_pdf_content, "application/pdf"),
            is_published=True,
        )
        del_res = self.client.delete(f"/api/content/admin/study-materials/{material.id}/")
        self.assertEqual(del_res.status_code, 403)

    def test_admin_deletion_cleans_up_physical_file(self):
        self.client.force_authenticate(user=self.admin)
        material = StudyMaterial.objects.create(
            exam=self.exam,
            title="To Delete",
            material_type="PDF",
            file=SimpleUploadedFile("todelete.pdf", self.valid_pdf_content, "application/pdf"),
            is_published=True,
        )
        file_path = material.file.name
        self.assertTrue(material.file.storage.exists(file_path))

        del_res = self.client.delete(f"/api/content/admin/study-materials/{material.id}/")
        self.assertEqual(del_res.status_code, 204)
        self.assertFalse(StudyMaterial.objects.filter(id=material.id).exists())
        self.assertFalse(material.file.storage.exists(file_path))

    # -------------------------------------------------------------
    # STUDENT DOWNLOAD SECURITY
    # -------------------------------------------------------------
    def test_student_download_published_material_increments_and_succeeds(self):
        material = StudyMaterial.objects.create(
            exam=self.exam,
            title="Published Guide",
            material_type="PDF",
            file=SimpleUploadedFile("guide.pdf", self.valid_pdf_content, "application/pdf"),
            is_published=True,
            download_count=0,
        )
        res = self.client.get(f"/api/content/study-materials/{material.id}/download/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("download_url", res.data)
        self.assertEqual(res.data["download_count"], 1)

        material.refresh_from_db()
        self.assertEqual(material.download_count, 1)

    def test_student_download_draft_material_returns_404(self):
        material = StudyMaterial.objects.create(
            exam=self.exam,
            title="Draft Guide",
            material_type="PDF",
            file=SimpleUploadedFile("draft.pdf", self.valid_pdf_content, "application/pdf"),
            is_published=False,
            download_count=0,
        )
        res = self.client.get(f"/api/content/study-materials/{material.id}/download/")
        self.assertEqual(res.status_code, 404)

    def test_missing_physical_file_returns_404_not_500(self):
        material = StudyMaterial.objects.create(
            exam=self.exam,
            title="Missing Physical File",
            material_type="PDF",
            file=SimpleUploadedFile("ghost.pdf", self.valid_pdf_content, "application/pdf"),
            is_published=True,
        )
        # Delete file from disk while DB record remains
        if material.file and material.file.storage.exists(material.file.name):
            material.file.storage.delete(material.file.name)

        res = self.client.get(f"/api/content/study-materials/{material.id}/download/")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.data["detail"], "File no longer exists.")

    def test_streaming_download_returns_file_response_with_nosniff_header(self):
        material = StudyMaterial.objects.create(
            exam=self.exam,
            title="Stream Material",
            material_type="PDF",
            file=SimpleUploadedFile("stream.pdf", self.valid_pdf_content, "application/pdf"),
            is_published=True,
        )
        res = self.client.get(f"/api/content/study-materials/{material.id}/download/?stream=true")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["X-Content-Type-Options"], "nosniff")
        self.assertIn("attachment", res["Content-Disposition"])
        self.assertIn(f"mockii_material_{material.id}.pdf", res["Content-Disposition"])
        for closer in getattr(res, "_resource_closers", []):
            try:
                closer()
            except Exception:
                pass

    # -------------------------------------------------------------
    # SAFE REPLACEMENT BEHAVIOR
    # -------------------------------------------------------------
    def test_valid_replacement_updates_file_and_deletes_old(self):
        self.client.force_authenticate(user=self.admin)
        material = StudyMaterial.objects.create(
            exam=self.exam,
            title="Replace Test",
            material_type="PDF",
            file=SimpleUploadedFile("old_doc.pdf", self.valid_pdf_content, "application/pdf"),
            is_published=True,
        )
        old_path = material.file.name
        self.assertTrue(material.file.storage.exists(old_path))

        new_uploaded = SimpleUploadedFile(
            "new_doc.pdf",
            self.valid_pdf_content + b"\n%MoreContent",
            content_type="application/pdf",
        )
        res = self.client.patch(
            f"/api/content/admin/study-materials/{material.id}/",
            {"file": new_uploaded},
            format="multipart",
        )
        self.assertEqual(res.status_code, 200)
        material.refresh_from_db()
        new_path = material.file.name
        self.assertNotEqual(old_path, new_path)
        self.assertTrue(material.file.storage.exists(new_path))
        self.assertFalse(material.file.storage.exists(old_path))

    def test_invalid_replacement_keeps_old_file_intact(self):
        self.client.force_authenticate(user=self.admin)
        material = StudyMaterial.objects.create(
            exam=self.exam,
            title="Replace Test 2",
            material_type="PDF",
            file=SimpleUploadedFile("safe.pdf", self.valid_pdf_content, "application/pdf"),
            is_published=True,
        )
        old_path = material.file.name
        self.assertTrue(material.file.storage.exists(old_path))

        # Try to replace with invalid executable
        bad_uploaded = SimpleUploadedFile(
            "bad.exe",
            b"MZExecutable",
            content_type="application/x-msdownload",
        )
        res = self.client.patch(
            f"/api/content/admin/study-materials/{material.id}/",
            {"file": bad_uploaded},
            format="multipart",
        )
        self.assertEqual(res.status_code, 400)

        # Old file must still exist and belong to the material!
        material.refresh_from_db()
        self.assertEqual(material.file.name, old_path)
        self.assertTrue(material.file.storage.exists(old_path))

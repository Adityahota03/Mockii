import os
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import Exam, ExamCategory, PreviousYearPaper

User = get_user_model()


class PreviousYearPaperModelTests(TestCase):

    def setUp(self):
        self.category = ExamCategory.objects.create(
            name="Government",
            slug="government-model-test",
            description="Government exams"
        )
        self.exam = Exam.objects.create(
            category=self.category,
            name="SSC CGL",
            slug="ssc-cgl-model-test",
            short_description="Combined Graduate Level"
        )

    def test_model_creation(self):
        paper = PreviousYearPaper.objects.create(
            exam=self.exam,
            title="SSC CGL 2025 Tier 1",
            year=2025,
            category="SSC CGL",
            paper_type="QUESTION_PAPER",
            is_published=False
        )

        self.assertEqual(paper.title, "SSC CGL 2025 Tier 1")
        self.assertEqual(paper.year, 2025)
        self.assertEqual(paper.category, "SSC CGL")
        self.assertEqual(paper.paper_type, "QUESTION_PAPER")
        self.assertFalse(paper.is_published)
        self.assertEqual(paper.download_count, 0)
        self.assertEqual(str(paper), "SSC CGL 2025 Tier 1 - 2025")


class AdminPreviousYearPaperApiTests(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin_pyp@mockii.com",
            password="adminpassword123",
            role=User.Roles.ADMIN
        )
        self.super_admin = User.objects.create_user(
            email="superadmin_pyp@mockii.com",
            password="superpassword123",
            role=User.Roles.SUPER_ADMIN
        )
        self.student = User.objects.create_user(
            email="student_pyp@mockii.com",
            password="studentpassword123",
            role=User.Roles.STUDENT
        )
        self.category = ExamCategory.objects.create(
            name="Engineering",
            slug="engineering-pyp",
            description="Engineering entrance exams"
        )
        self.exam = Exam.objects.create(
            category=self.category,
            name="JEE Advanced",
            slug="jee-advanced-pyp",
            short_description="Joint Entrance Examination Advanced"
        )
        self.valid_pdf = SimpleUploadedFile(
            name="jee_2023_paper1.pdf",
            content=b"%PDF-1.4 sample jee paper content for testing",
            content_type="application/pdf"
        )

    def test_admin_list_papers(self):
        self.client.force_authenticate(user=self.admin)
        PreviousYearPaper.objects.create(
            exam=self.exam,
            title="JEE Advanced 2022 Paper 1",
            year=2022,
            category="Physics",
            paper_type="QUESTION_PAPER",
            is_published=True
        )
        PreviousYearPaper.objects.create(
            exam=self.exam,
            title="JEE Advanced 2021 Paper 1",
            year=2021,
            category="Mathematics",
            paper_type="QUESTION_PAPER",
            is_published=False
        )

        url = reverse("admin-previous-year-paper-list-create")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 2)
        self.assertEqual(len(res.data["results"]), 2)

    def test_admin_create_paper_success(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("admin-previous-year-paper-list-create")
        data = {
            "exam": self.exam.id,
            "title": "JEE Advanced 2023 Paper 1",
            "year": 2023,
            "category": "Physics",
            "paper_type": "QUESTION_PAPER",
            "description": "Original question paper with instructions",
            "file": self.valid_pdf,
            "is_published": False,
        }
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "JEE Advanced 2023 Paper 1")
        self.assertEqual(response.data["year"], 2023)
        self.assertEqual(response.data["paper_type"], "QUESTION_PAPER")
        self.assertFalse(response.data["is_published"])
        self.assertGreater(response.data["file_size"], 0)
        self.assertIn("previous_year_papers/exam_", response.data["file_url"])

    def test_super_admin_can_access_admin_api(self):
        self.client.force_authenticate(user=self.super_admin)
        url = reverse("admin-previous-year-paper-list-create")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_admin_get_detail(self):
        self.client.force_authenticate(user=self.admin)
        paper = PreviousYearPaper.objects.create(
            exam=self.exam,
            title="JEE Detail Test",
            year=2020,
            category="Chemistry",
            paper_type="QUESTION_PAPER",
            is_published=False
        )
        url = reverse("admin-previous-year-paper-detail", kwargs={"paper_id": paper.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["title"], "JEE Detail Test")

    def test_admin_update_paper_metadata(self):
        self.client.force_authenticate(user=self.admin)
        paper = PreviousYearPaper.objects.create(
            exam=self.exam,
            title="Old Paper Title",
            year=2020,
            category="Physics",
            paper_type="QUESTION_PAPER",
            description="Old description",
            is_published=False
        )
        url = reverse("admin-previous-year-paper-detail", kwargs={"paper_id": paper.id})
        update_data = {
            "title": "Updated Paper Title",
            "description": "Updated description",
            "year": 2021,
            "category": "Modern Physics",
        }
        res = self.client.patch(url, update_data, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["title"], "Updated Paper Title")
        self.assertEqual(res.data["year"], 2021)
        self.assertEqual(res.data["category"], "Modern Physics")

    def test_admin_update_pdf_replacement(self):
        self.client.force_authenticate(user=self.admin)
        old_pdf = SimpleUploadedFile(
            name="paper_old.pdf",
            content=b"%PDF-1.4 old pdf content",
            content_type="application/pdf"
        )
        paper = PreviousYearPaper.objects.create(
            exam=self.exam,
            title="Paper for Replacement",
            year=2021,
            category="Maths",
            file=old_pdf,
            file_size=len(old_pdf),
            is_published=False
        )
        old_file_name = paper.file.name
        old_file_path = paper.file.path if hasattr(paper.file, "path") else None

        new_pdf = SimpleUploadedFile(
            name="paper_new.pdf",
            content=b"%PDF-1.4 newly replaced pdf content",
            content_type="application/pdf"
        )
        url = reverse("admin-previous-year-paper-detail", kwargs={"paper_id": paper.id})
        res = self.client.patch(url, {"file": new_pdf}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        paper.refresh_from_db()
        self.assertNotEqual(paper.file.name, old_file_name)
        self.assertTrue(paper.file.name.endswith(".pdf"))
        if old_file_path and os.path.exists(old_file_path):
            # The old file should have been cleaned up
            self.assertFalse(os.path.exists(old_file_path))

    def test_admin_delete_paper(self):
        self.client.force_authenticate(user=self.admin)
        test_pdf = SimpleUploadedFile(
            name="to_delete.pdf",
            content=b"%PDF-1.4 to be deleted content",
            content_type="application/pdf"
        )
        paper = PreviousYearPaper.objects.create(
            exam=self.exam,
            title="Delete Paper",
            year=2019,
            category="General",
            paper_type="PDF",
            file=test_pdf,
            file_size=len(test_pdf),
            is_published=True
        )
        file_path = paper.file.path if hasattr(paper.file, "path") else None

        url = reverse("admin-previous-year-paper-detail", kwargs={"paper_id": paper.id})
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PreviousYearPaper.objects.filter(id=paper.id).exists())
        if file_path and os.path.exists(file_path):
            self.assertFalse(os.path.exists(file_path))

    def test_admin_publish_and_unpublish_toggle(self):
        self.client.force_authenticate(user=self.admin)
        paper = PreviousYearPaper.objects.create(
            exam=self.exam,
            title="Toggle Paper",
            year=2020,
            category="General",
            paper_type="PDF",
            is_published=False
        )
        url = reverse("admin-previous-year-paper-publish", kwargs={"paper_id": paper.id})

        # Publish
        res = self.client.patch(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data["is_published"])
        paper.refresh_from_db()
        self.assertTrue(paper.is_published)

        # Unpublish
        res2 = self.client.patch(url)
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertFalse(res2.data["is_published"])
        paper.refresh_from_db()
        self.assertFalse(paper.is_published)

    def test_admin_filters(self):
        self.client.force_authenticate(user=self.admin)
        paper1 = PreviousYearPaper.objects.create(
            exam=self.exam,
            title="JEE Advanced 2022 Paper",
            year=2022,
            category="Chemistry",
            paper_type="QUESTION_PAPER",
            is_published=True
        )
        paper2 = PreviousYearPaper.objects.create(
            exam=self.exam,
            title="JEE Advanced 2021 Solution",
            year=2021,
            category="Mathematics",
            paper_type="SOLUTION",
            is_published=False
        )

        url = reverse("admin-previous-year-paper-list-create")

        # Filter by year
        res_year = self.client.get(url, {"year": 2022})
        self.assertEqual(len(res_year.data["results"]), 1)
        self.assertEqual(res_year.data["results"][0]["id"], paper1.id)

        # Filter by paper_type
        res_type = self.client.get(url, {"paper_type": "SOLUTION"})
        self.assertEqual(len(res_type.data["results"]), 1)
        self.assertEqual(res_type.data["results"][0]["id"], paper2.id)

        # Filter by category
        res_cat = self.client.get(url, {"category": "Chemistry"})
        self.assertEqual(len(res_cat.data["results"]), 1)
        self.assertEqual(res_cat.data["results"][0]["id"], paper1.id)

        # Filter by is_published
        res_pub = self.client.get(url, {"is_published": "true"})
        self.assertEqual(len(res_pub.data["results"]), 1)
        self.assertEqual(res_pub.data["results"][0]["id"], paper1.id)

    def test_file_validation_rejects_non_pdf(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("admin-previous-year-paper-list-create")

        # Test DOCX
        docx_file = SimpleUploadedFile(
            name="paper.docx",
            content=b"word document content",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        data = {
            "exam": self.exam.id,
            "title": "Invalid File Test",
            "year": 2022,
            "category": "Maths",
            "file": docx_file,
        }
        res_docx = self.client.post(url, data, format="multipart")
        self.assertEqual(res_docx.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", res_docx.data)

        # Test EXE
        exe_file = SimpleUploadedFile(
            name="malicious.exe",
            content=b"MZ dummy binary executable",
            content_type="application/x-msdownload"
        )
        data["file"] = exe_file
        res_exe = self.client.post(url, data, format="multipart")
        self.assertEqual(res_exe.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", res_exe.data)

    def test_file_validation_rejects_oversized_file(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("admin-previous-year-paper-list-create")
        # 21 MB dummy file
        large_size = 21 * 1024 * 1024
        large_content = b"%PDF-1.4 " + (b"0" * (large_size - 9))
        large_file = SimpleUploadedFile(
            name="large_paper.pdf",
            content=large_content,
            content_type="application/pdf"
        )
        data = {
            "exam": self.exam.id,
            "title": "Oversized Paper Test",
            "year": 2022,
            "category": "Maths",
            "file": large_file,
        }
        res = self.client.post(url, data, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", res.data)

    def test_student_cannot_access_admin_endpoints(self):
        self.client.force_authenticate(user=self.student)
        url = reverse("admin-previous-year-paper-list-create")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_access_admin_endpoints(self):
        url = reverse("admin-previous-year-paper-list-create")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class StudentPreviousYearPaperApiTests(APITestCase):

    def setUp(self):
        self.category = ExamCategory.objects.create(
            name="Medical",
            slug="medical-pyp",
            description="Medical exams"
        )
        self.exam = Exam.objects.create(
            category=self.category,
            name="NEET UG",
            slug="neet-ug-pyp",
            short_description="National Eligibility cum Entrance Test"
        )
        self.valid_pdf = SimpleUploadedFile(
            name="neet_2023.pdf",
            content=b"%PDF-1.4 sample neet question paper content",
            content_type="application/pdf"
        )
        self.published_paper = PreviousYearPaper.objects.create(
            exam=self.exam,
            title="NEET UG 2023 Question Paper",
            description="Official NEET question paper",
            year=2023,
            category="Physics",
            paper_type="QUESTION_PAPER",
            file=self.valid_pdf,
            file_size=len(self.valid_pdf),
            is_published=True,
            download_count=0
        )
        self.draft_paper = PreviousYearPaper.objects.create(
            exam=self.exam,
            title="NEET UG 2024 Leaked Draft",
            description="Unpublished confidential paper",
            year=2024,
            category="Biology",
            paper_type="QUESTION_PAPER",
            is_published=False,
            download_count=0
        )

    def test_student_list_excludes_draft_papers(self):
        url = reverse("previous-year-papers")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.published_paper.id)
        self.assertEqual(data[0]["title"], "NEET UG 2023 Question Paper")
        self.assertNotIn("is_published", data[0])

    def test_student_search_and_filters(self):
        url = reverse("previous-year-papers")

        # Search matching title
        res_search = self.client.get(url, {"search": "NEET UG 2023"})
        self.assertEqual(len(res_search.data), 1)

        # Search matching exam name
        res_exam_search = self.client.get(url, {"search": "NEET"})
        self.assertEqual(len(res_exam_search.data), 1)

        # Search matching category
        res_cat_search = self.client.get(url, {"search": "Physics"})
        self.assertEqual(len(res_cat_search.data), 1)

        # Search non-matching
        res_empty = self.client.get(url, {"search": "UPSC Civil Services"})
        self.assertEqual(len(res_empty.data), 0)

        # Filter by exam
        res_exam = self.client.get(url, {"exam": self.exam.id})
        self.assertEqual(len(res_exam.data), 1)

        # Filter by year
        res_year = self.client.get(url, {"year": 2023})
        self.assertEqual(len(res_year.data), 1)
        res_wrong_year = self.client.get(url, {"year": 2020})
        self.assertEqual(len(res_wrong_year.data), 0)

        # Filter by category
        res_cat = self.client.get(url, {"category": "Physics"})
        self.assertEqual(len(res_cat.data), 1)

    def test_student_detail_view_and_draft_protection(self):
        # Published detail works
        pub_url = reverse("previous-year-paper-detail", kwargs={"paper_id": self.published_paper.id})
        res_pub = self.client.get(pub_url)
        self.assertEqual(res_pub.status_code, status.HTTP_200_OK)
        self.assertEqual(res_pub.data["title"], self.published_paper.title)
        self.assertNotIn("is_published", res_pub.data)

        # Draft detail returns 404
        draft_url = reverse("previous-year-paper-detail", kwargs={"paper_id": self.draft_paper.id})
        res_draft = self.client.get(draft_url)
        self.assertEqual(res_draft.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_download_and_atomic_increment(self):
        dl_url = reverse("previous-year-paper-download", kwargs={"paper_id": self.published_paper.id})

        # Initial download
        res1 = self.client.get(dl_url)
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(res1.data["download_count"], 1)
        self.assertIn("download_url", res1.data)

        # Second download increments
        res2 = self.client.get(dl_url)
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data["download_count"], 2)

        # Verify in database
        self.published_paper.refresh_from_db()
        self.assertEqual(self.published_paper.download_count, 2)

        # Draft download returns 404
        draft_dl_url = reverse("previous-year-paper-download", kwargs={"paper_id": self.draft_paper.id})
        res_draft = self.client.get(draft_dl_url)
        self.assertEqual(res_draft.status_code, status.HTTP_404_NOT_FOUND)

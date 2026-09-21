from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import Exam, ExamCategory, StudyMaterial

User = get_user_model()


class StudentStudyMaterialApiTests(APITestCase):

    def setUp(self):
        self.category = ExamCategory.objects.create(
            name="Government",
            slug="government",
            description="Gov exams"
        )
        self.exam = Exam.objects.create(
            category=self.category,
            name="SSC CGL",
            slug="ssc-cgl",
            short_description="Combined Graduate Level"
        )

        test_pdf = SimpleUploadedFile(
            name="ssc_maths.pdf",
            content=b"%PDF-1.4 test study material content",
            content_type="application/pdf"
        )

        self.published_material = StudyMaterial.objects.create(
            exam=self.exam,
            title="SSC Maths Guide",
            description="Complete math notes",
            category="Mathematics",
            material_type="PDF",
            file=test_pdf,
            file_size=len(test_pdf),
            is_published=True,
            download_count=0
        )

        self.draft_material = StudyMaterial.objects.create(
            exam=self.exam,
            title="Secret Draft Formula",
            description="Unpublished draft",
            category="Physics",
            material_type="PDF",
            is_published=False,
            download_count=0
        )

    def test_list_excludes_draft_materials(self):
        url = reverse("student-study-material-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Results are paginated
        results = response.data.get("results", [])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.published_material.id)
        self.assertEqual(results[0]["title"], "SSC Maths Guide")
        self.assertNotIn("is_published", results[0])
        self.assertNotIn("file_url", results[0])

    def test_search_and_filtering(self):
        url = reverse("student-study-material-list")

        # Search matching title
        res = self.client.get(url, {"search": "Maths"})
        self.assertEqual(len(res.data.get("results", [])), 1)

        # Search non-matching
        res_empty = self.client.get(url, {"search": "Biology"})
        self.assertEqual(len(res_empty.data.get("results", [])), 0)

        # Filter by exam
        res_exam = self.client.get(url, {"exam": self.exam.id})
        self.assertEqual(len(res_exam.data.get("results", [])), 1)

        # Filter by category
        res_cat = self.client.get(url, {"category": "Mathematics"})
        self.assertEqual(len(res_cat.data.get("results", [])), 1)

    def test_detail_view(self):
        # Published material detail
        url_pub = reverse("student-study-material-detail", kwargs={"material_id": self.published_material.id})
        res_pub = self.client.get(url_pub)
        self.assertEqual(res_pub.status_code, status.HTTP_200_OK)
        self.assertEqual(res_pub.data["title"], "SSC Maths Guide")
        self.assertNotIn("is_published", res_pub.data)

        # Draft material detail -> 404
        url_draft = reverse("student-study-material-detail", kwargs={"material_id": self.draft_material.id})
        res_draft = self.client.get(url_draft)
        self.assertEqual(res_draft.status_code, status.HTTP_404_NOT_FOUND)

    def test_download_counter_and_url(self):
        download_url = reverse(
            "student-study-material-download",
            kwargs={"material_id": self.published_material.id}
        )

        res1 = self.client.get(download_url)
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(res1.data["download_count"], 1)
        self.assertIn("download_url", res1.data)
        self.assertTrue(res1.data["download_url"].endswith(".pdf"))

        # Second download increments again
        res2 = self.client.get(download_url)
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data["download_count"], 2)

        # Attempt to download draft -> 404
        draft_dl_url = reverse(
            "student-study-material-download",
            kwargs={"material_id": self.draft_material.id}
        )
        res_draft = self.client.get(draft_dl_url)
        self.assertEqual(res_draft.status_code, status.HTTP_404_NOT_FOUND)

    def test_s3_presigned_url_generator(self):
        from content.utils.s3 import generate_study_material_url
        with self.settings(
            AWS_STORAGE_BUCKET_NAME="test-mockii-bucket",
            AWS_S3_REGION_NAME="ap-south-1",
            AWS_ACCESS_KEY_ID="test-key",
            AWS_SECRET_ACCESS_KEY="test-secret"
        ):
            url = generate_study_material_url("study_materials/exam_1/test.pdf", expiration=300)
            self.assertIn("test-mockii-bucket", url)
            self.assertIn("study_materials/exam_1/test.pdf", url)
            self.assertIn("X-Amz-Expires=300", url)
            self.assertIn("X-Amz-Signature=", url)

    def test_migrate_study_materials_command_dry_run(self):
        from io import StringIO
        from django.core.management import call_command

        out = StringIO()
        call_command("migrate_study_materials_to_s3", dry_run=True, stdout=out)
        output = out.getvalue()
        self.assertIn("Found", output)
        self.assertIn("DRY RUN enabled", output)
        self.assertIn("Migration Summary", output)

    def test_verify_study_materials_command(self):
        from io import StringIO
        from django.core.management import call_command

        out = StringIO()
        call_command("verify_study_materials_s3", stdout=out)
        output = out.getvalue()
        self.assertIn("Checking", output)
        self.assertIn("Verification Summary", output)

"""Debug the mock-test list 500 and question delete 500."""
import os, sys, django
sys.path.insert(0, 'D:\\Mockii\\backend')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_test'
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from content.models import Exam, ExamCategory, MockTest, Question

User = get_user_model()

# --- Probe 1: mock-test list 500 ---
student = User.objects.create_user(
    email='debug_mock@test.com', password='Pass123!',
    role=User.Roles.STUDENT, is_active=True
)
cat = ExamCategory.objects.create(name='Debug Cat', slug='debug-cat-x1')
exam = Exam.objects.create(name='Debug Exam', slug='debug-exam-x1', category=cat, is_active=True)
MockTest.objects.create(
    exam=exam, title='Debug MT', slug='debug-mt-x1',
    duration_minutes=60, total_marks=100, is_published=True
)

c = APIClient()
c.force_authenticate(user=student)
resp = c.get('/api/content/mock-tests/')
print('Mock-test list status:', resp.status_code)
if resp.status_code != 200:
    print('Response:', resp.data)

# --- Probe 2: question delete 500 ---
admin = User.objects.create_user(
    email='debug_admin@test.com', password='Pass123!',
    role=User.Roles.ADMIN, is_staff=True, is_active=True
)
q = Question.objects.create(question_text='Debug Delete Q', question_type='MCQ')
c2 = APIClient()
c2.force_authenticate(user=admin)
resp2 = c2.delete(f'/api/content/admin/questions/{q.id}/')
print('Delete question status:', resp2.status_code)
if resp2.status_code not in (200, 204):
    print('Response:', resp2.data if hasattr(resp2, 'data') else resp2.content)

# --- Probe 3: publish mock test ---
mt_unp = MockTest.objects.create(
    exam=exam, title='Unpub', slug='unpub-x1',
    duration_minutes=60, total_marks=100, is_published=False
)
resp3 = c2.patch(f'/api/content/admin/mock-tests/{mt_unp.id}/publish/', {'is_published': True}, format='json')
print('Publish mock test status:', resp3.status_code)
if resp3.status_code not in (200, 201):
    print('Publish response:', resp3.data if hasattr(resp3, 'data') else resp3.content)

# --- Probe 4: duplicate slug ---
from content.models import ExamCategory
cat2 = ExamCategory.objects.create(name='Slug Cat', slug='slug-cat-x1')
Exam.objects.create(name='Original', slug='dup-slug-x1', category=cat2)
resp4 = c2.post('/api/content/admin/exams/', {
    'name': 'Duplicate', 'slug': 'dup-slug-x1', 'category': cat2.id
}, format='json')
print('Duplicate slug status:', resp4.status_code)
if resp4.status_code == 201:
    print('  BUG: duplicate slug was accepted!')
else:
    print('  OK: duplicate slug rejected:', resp4.data)

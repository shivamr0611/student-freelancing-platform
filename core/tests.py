"""
core/tests.py 
Run:    python manage.py test core -v 2
Result: 20 tests, ok

"""

from django.test import TestCase, Client
from django.urls import reverse
from datetime import date, timedelta
from decimal import Decimal
from django.db import IntegrityError

from core.models import (
    CustomUser, StudentProfile, CompanyProfile,
    Job, Application, Submission, Payment, PlatformSettings,
)


# ─── Shared helpers ───────────────────────────────────────────────────────────

def make_student(username, n=0):
    """Create a CustomUser with role='student' and a linked StudentProfile."""
    u = CustomUser.objects.create_user(
        username=username, password='TestPass@123', role='student'
    )
    sp = StudentProfile.objects.create(
        user=u, full_name=f'Student {n}',
        email=f'{username}@test.com',
        college='Test College',
        skills='Python, Django, MySQL',
    )
    return u, sp


def make_company(username):
    """Create a CustomUser with role='company' and a linked CompanyProfile."""
    u = CustomUser.objects.create_user(
        username=username, password='TestPass@123', role='company'
    )
    cp = CompanyProfile.objects.create(
        user=u,
        company_name=f'{username} Corp.',
        email=f'{username}@test.com',
    )
    return u, cp


def make_job(company_profile, title='Test Job', budget=8000):
    """Create an open Job linked to the given CompanyProfile."""
    return Job.objects.create(
        company=company_profile,
        title=title,
        description='Detailed job description for testing purposes.',
        required_skills='Python, Django',
        budget=Decimal(str(budget)),
        deadline=date.today() + timedelta(days=30),
    )


# ═════════════════════════════════════════════════════════════════════════════
# TC-UT-01 to TC-UT-06 — Authentication Module
# ═════════════════════════════════════════════════════════════════════════════

class AuthenticationTests(TestCase):
    """Unit tests for login_view, register_student, register_company, role_required."""

    def setUp(self):
        self.client = Client()
        # Existing active student
        self.student_user, self.student_profile = make_student('exist_student')
        # Existing company
        self.company_user, self.company_profile = make_company('exist_company')
        # Deactivated student
        self.inactive_user = CustomUser.objects.create_user(
            username='inactiveuser',
            password='TestPass@123',
            role='student',
            is_active=False,
        )

    # ── TC-UT-01 ──────────────────────────────────────────────────────────────
    def test_TC_UT_01_valid_student_registration(self):
        """
        TC-UT-01 | Valid student registration
        Input   : New username, valid passwords, all required fields
        Expected: HTTP 302 redirect + CustomUser + StudentProfile created
        """
        response = self.client.post(reverse('register_student'), {
            'username':   'newstudent',
            'full_name':  'New Student',
            'email':      'new@test.com',
            'college':    'New College',
            'skills':     'Python, Django',
            'password1':  'TestPass@123',
            'password2':  'TestPass@123',
        })
        # Should redirect (HTTP 302) on success
        self.assertEqual(response.status_code, 302,
            "Expected redirect after valid registration")
        # CustomUser must exist with correct role
        self.assertTrue(CustomUser.objects.filter(username='newstudent').exists(),
            "CustomUser was not created")
        user = CustomUser.objects.get(username='newstudent')
        self.assertEqual(user.role, 'student')
        self.assertTrue(user.is_active)
        # StudentProfile must be linked
        self.assertTrue(
            StudentProfile.objects.filter(full_name='New Student').exists(),
            "StudentProfile was not created"
        )

    # ── TC-UT-02 ──────────────────────────────────────────────────────────────
    def test_TC_UT_02_duplicate_username_rejected(self):
        """
        TC-UT-02 | Duplicate username registration
        Input   : Username 'exist_student' (already in DB)
        Expected: HTTP 200 (form re-render), no new user created
        """
        initial_count = CustomUser.objects.count()
        response = self.client.post(reverse('register_student'), {
            'username':  'exist_student',  # already taken
            'full_name': 'Duplicate',
            'email':     'dup@test.com',
            'college':   'Dup College',
            'skills':    'Python',
            'password1': 'TestPass@123',
            'password2': 'TestPass@123',
        })
        self.assertEqual(response.status_code, 200,
            "Expected form re-render (200), not a redirect")
        self.assertEqual(CustomUser.objects.count(), initial_count,
            "No new user should be created on duplicate username")

    # ── TC-UT-03 ──────────────────────────────────────────────────────────────
    def test_TC_UT_03_valid_login_redirects_to_dashboard(self):
        """
        TC-UT-03 | Valid login with correct credentials
        Input   : username='exist_student', password='TestPass@123'
        Expected: HTTP 302 → home_redirect → student_home (follow chain)
        """
        response = self.client.post(reverse('login'), {
            'username': 'exist_student',
            'password': 'TestPass@123',
        }, follow=True)
        # After following redirects, final URL must be student_home
        self.assertEqual(response.status_code, 200)
        final_url = response.redirect_chain[-1][0]
        self.assertIn('/student/', final_url,
            "Should redirect to Student dashboard after login")

    # ── TC-UT-04 ──────────────────────────────────────────────────────────────
    def test_TC_UT_04_login_wrong_password_rejected(self):
        """
        TC-UT-04 | Login with wrong password
        Input   : Correct username, wrong password 'WrongPass999'
        Expected: HTTP 200 (stays on login), error message shown
        """
        response = self.client.post(reverse('login'), {
            'username': 'exist_student',
            'password': 'WrongPass999',
        })
        self.assertEqual(response.status_code, 200,
            "Wrong password should NOT redirect")
        self.assertContains(response, 'Invalid username or password',
            msg_prefix="Error message must be displayed")

    # ── TC-UT-05 ──────────────────────────────────────────────────────────────
    def test_TC_UT_05_student_accessing_company_url_blocked(self):
        """
        TC-UT-05 | Role guard — Student accessing Company dashboard
        Input   : Student logged in, GET /company/
        Expected: HTTP 302 redirect to /login/ (role mismatch)
        """
        self.client.force_login(self.student_user)
        response = self.client.get(reverse('company_home'))
        self.assertRedirects(response, reverse('login'),
            fetch_redirect_response=False,
            msg_prefix="Student should be blocked from company URL")

    # ── TC-UT-06 ──────────────────────────────────────────────────────────────
    def test_TC_UT_06_deactivated_user_cannot_login(self):
        """
        TC-UT-06 | Deactivated account login attempt
        Input   : is_active=False user credentials
        Expected: HTTP 200 (no redirect), user stays on login page
        """
        response = self.client.post(reverse('login'), {
            'username': 'inactiveuser',
            'password': 'TestPass@123',
        })
        self.assertEqual(response.status_code, 200,
            "Deactivated user should not be redirected to dashboard")
        self.assertTemplateUsed(response, 'auth/login.html',
            "Login template should be re-rendered")


# ═════════════════════════════════════════════════════════════════════════════
# TC-UT-07 to TC-UT-10 — Model Unit Tests
# ═════════════════════════════════════════════════════════════════════════════

class ModelTests(TestCase):
    """Direct unit tests on model methods and database constraints."""

    def setUp(self):
        self.student_user, self.student_profile = make_student('modelstudent')
        self.company_user, self.company_profile = make_company('modelcompany')
        self.job = make_job(self.company_profile)

    # ── TC-UT-07 ──────────────────────────────────────────────────────────────
    def test_TC_UT_07_student_profile_skills_list(self):
        """
        TC-UT-07 | StudentProfile.skills_list() method
        Input   : skills = 'Python, Django, MySQL'
        Expected: Returns list ['Python', 'Django', 'MySQL'] (3 items)
        """
        result = self.student_profile.skills_list()
        self.assertIsInstance(result, list, "skills_list() must return a list")
        self.assertEqual(len(result), 3, "Expected 3 skills")
        self.assertIn('Python', result)
        self.assertIn('Django', result)
        self.assertIn('MySQL',  result)

    # ── TC-UT-08 ──────────────────────────────────────────────────────────────
    def test_TC_UT_08_job_skills_list(self):
        """
        TC-UT-08 | Job.skills_list() method
        Input   : required_skills = 'Python, Django'
        Expected: Returns list ['Python', 'Django'] (2 items)
        """
        result = self.job.skills_list()
        self.assertIsInstance(result, list)
        self.assertEqual(result, ['Python', 'Django'])

    # ── TC-UT-09 ──────────────────────────────────────────────────────────────
    def test_TC_UT_09_payment_defaults_to_not_paid(self):
        """
        TC-UT-09 | Payment model default values
        Input   : Payment.objects.create(application, amount=5000)
        Expected: status='not_paid', paid_at=None
        """
        app = Application.objects.create(
            job=self.job,
            student=self.student_profile,
            proposal='Test proposal for payment model',
        )
        payment = Payment.objects.create(
            application=app,
            amount=Decimal('5000.00'),
        )
        self.assertEqual(payment.status, 'not_paid',
            "Payment status must default to 'not_paid'")
        self.assertIsNone(payment.paid_at,
            "paid_at must be None until payment is released")

    # ── TC-UT-10 ──────────────────────────────────────────────────────────────
    def test_TC_UT_10_application_unique_together_constraint(self):
        """
        TC-UT-10 | Application unique_together (job, student) constraint
        Input   : Create two Applications with same job + student
        Expected: Second create raises IntegrityError
        """
        Application.objects.create(
            job=self.job,
            student=self.student_profile,
            proposal='First application',
        )
        with self.assertRaises(IntegrityError,
            msg="Duplicate application must raise IntegrityError"):
            Application.objects.create(
                job=self.job,
                student=self.student_profile,
                proposal='Second application — must be blocked',
            )


# ═════════════════════════════════════════════════════════════════════════════
# TC-UT-11 to TC-UT-14 — Student Module
# ═════════════════════════════════════════════════════════════════════════════

class StudentModuleTests(TestCase):
    """Unit tests for student_home, student_apply, student_submit_work views."""

    def setUp(self):
        self.client = Client()
        self.student_user, self.student_profile = make_student('viewstudent')
        self.company_user, self.company_profile = make_company('viewcompany')
        self.job = make_job(self.company_profile, title='Browse Test Job')
        self.client.force_login(self.student_user)

    # ── TC-UT-11 ──────────────────────────────────────────────────────────────
    def test_TC_UT_11_student_home_page_loads(self):
        """
        TC-UT-11 | student_home view loads for logged-in student
        Input   : GET /student/ (authenticated as student)
        Expected: HTTP 200, job title visible, 'jobs' in context
        """
        response = self.client.get(reverse('student_home'))
        self.assertEqual(response.status_code, 200,
            "Browse Jobs page must return HTTP 200")
        self.assertContains(response, 'Browse Test Job',
            msg_prefix="Job title must appear on page")
        self.assertIn('jobs', response.context,
            "'jobs' must be in template context")

    # ── TC-UT-12 ──────────────────────────────────────────────────────────────
    def test_TC_UT_12_apply_for_job_creates_application(self):
        """
        TC-UT-12 | student_apply with valid proposal
        Input   : POST /student/apply/<job_id>/ with proposal text
        Expected: HTTP 302 → student_applications, Application created (pending)
        """
        response = self.client.post(
            reverse('student_apply', args=[self.job.id]),
            {'proposal': 'I have 2 years Django experience and can deliver this.'},
        )
        self.assertRedirects(response, reverse('student_applications'),
            msg_prefix="Should redirect to applications list on success")
        apps = Application.objects.filter(
            job=self.job, student=self.student_profile
        )
        self.assertTrue(apps.exists(), "Application record must be created")
        self.assertEqual(apps.first().status, 'pending',
            "New application status must be 'pending'")

    # ── TC-UT-13 ──────────────────────────────────────────────────────────────
    def test_TC_UT_13_duplicate_application_prevented(self):
        """
        TC-UT-13 | Duplicate application to same job
        Input   : Student applies twice to same job_id
        Expected: 302 → student_home (warning), still only 1 Application in DB
        """
        Application.objects.create(
            job=self.job,
            student=self.student_profile,
            proposal='First valid application',
        )
        response = self.client.post(
            reverse('student_apply', args=[self.job.id]),
            {'proposal': 'Second application — should be blocked'},
        )
        self.assertRedirects(response, reverse('student_home'),
            msg_prefix="Duplicate apply must redirect to student_home with warning")
        count = Application.objects.filter(
            job=self.job, student=self.student_profile
        ).count()
        self.assertEqual(count, 1, "Only 1 Application must exist in DB")

    # ── TC-UT-14 ──────────────────────────────────────────────────────────────
    def test_TC_UT_14_submit_work_creates_submission(self):
        """
        TC-UT-14 | student_submit_work for hired application
        Input   : POST /student/submit/<app_id>/ with notes
        Expected: 302 → active_jobs, Submission record created with correct notes
        """
        app = Application.objects.create(
            job=self.job,
            student=self.student_profile,
            proposal='Hired application',
            status='hired',
        )
        response = self.client.post(
            reverse('student_submit_work', args=[app.id]),
            {'notes': 'Completed. Code: github.com/test/project', 'file': ''},
        )
        self.assertRedirects(response, reverse('student_active_jobs'))
        self.assertTrue(
            Submission.objects.filter(application=app).exists(),
            "Submission record must be created"
        )
        sub = Submission.objects.get(application=app)
        self.assertIn('github.com', sub.notes,
            "Notes must be saved correctly")


# ═════════════════════════════════════════════════════════════════════════════
# TC-UT-15 to TC-UT-18 — Company Module
# ═════════════════════════════════════════════════════════════════════════════

class CompanyModuleTests(TestCase):
    """Unit tests for company_post_job, company_hire, company_release_payment."""

    def setUp(self):
        self.client = Client()
        self.company_user, self.company_profile = make_company('cotest')
        self.student_user, self.student_profile = make_student('coteststudent')
        self.job = make_job(self.company_profile, title='CO Test Job', budget=10000)
        self.client.force_login(self.company_user)

    # ── TC-UT-15 ──────────────────────────────────────────────────────────────
    def test_TC_UT_15_post_job_valid_creates_record(self):
        """
        TC-UT-15 | company_post_job with valid data
        Input   : POST /company/post-job/ with all required fields + budget>0
        Expected: 302 → company_home, Job created with status='open'
        """
        before = Job.objects.filter(company=self.company_profile).count()
        response = self.client.post(reverse('company_post_job'), {
            'title':           'New Valid Job',
            'description':     'Build a REST API for our mobile app with full CRUD.',
            'required_skills': 'Python, Django, MySQL',
            'budget':          '12000.00',
            'deadline':        (date.today() + timedelta(days=45)).strftime('%Y-%m-%d'),
            'category':        'Web Development',
        })
        self.assertRedirects(response, reverse('company_home'))
        after = Job.objects.filter(company=self.company_profile).count()
        self.assertEqual(after, before + 1, "One new Job must be created")
        job = Job.objects.get(title='New Valid Job')
        self.assertEqual(job.status, 'open')
        self.assertEqual(job.budget, Decimal('12000.00'))

    # ── TC-UT-16 ──────────────────────────────────────────────────────────────
    def test_TC_UT_16_post_job_zero_budget_rejected(self):
        """
        TC-UT-16 | company_post_job with budget = 0 (BVA Min-1)
        Input   : POST with budget='0'
        Expected: HTTP 200 (form error), no Job record created
        [DEFECT D1 — Fixed: added MinValueValidator to JobPostForm.budget]
        """
        before = Job.objects.count()
        response = self.client.post(reverse('company_post_job'), {
            'title':           'Zero Budget Job',
            'description':     'Job with invalid zero budget.',
            'required_skills': 'Python',
            'budget':          '0',
            'deadline':        (date.today() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'category':        'Test',
        })
        self.assertEqual(response.status_code, 200,
            "Zero budget must be rejected — form should re-render (200)")
        self.assertEqual(Job.objects.count(), before,
            "No Job record should be created with budget=0")

    # ── TC-UT-17 ──────────────────────────────────────────────────────────────
    def test_TC_UT_17_hire_applicant_auto_rejects_others(self):
        """
        TC-UT-17 | company_hire — hire one applicant, auto-reject others
        Input   : 3 students apply; company hires student 0
        Expected: student 0 = hired, students 1&2 = rejected; job = in_progress;
                  Payment record created for student 0
        """
        apps = []
        for i in range(3):
            _, sp = make_student(f'hire_s{i}', i)
            apps.append(Application.objects.create(
                job=self.job, student=sp, proposal=f'Proposal from student {i}'
            ))
        response = self.client.get(reverse('company_hire', args=[apps[0].id]))
        self.assertRedirects(response, reverse('company_applicants'))
        # Hired student
        apps[0].refresh_from_db()
        self.assertEqual(apps[0].status, 'hired', "First applicant must be hired")
        # Other applicants auto-rejected
        for a in apps[1:]:
            a.refresh_from_db()
            self.assertEqual(a.status, 'rejected',
                f"{a} must be auto-rejected")
        # Job updated
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, 'in_progress')
        # Payment record auto-created
        self.assertTrue(
            Payment.objects.filter(application=apps[0]).exists(),
            "Payment record must be created on hire"
        )
        payment = Payment.objects.get(application=apps[0])
        self.assertEqual(payment.amount, Decimal('10000.00'))
        self.assertEqual(payment.status, 'not_paid')

    # ── TC-UT-18 ──────────────────────────────────────────────────────────────
    def test_TC_UT_18_release_payment_updates_earnings_and_job(self):
        """
        TC-UT-18 | company_release_payment — credits student, marks job done
        Input   : Submission exists; GET /company/release-payment/<id>/
        Expected: Payment.status='paid', student.earnings += amount,
                  job.status='completed'
        """
        app = Application.objects.create(
            job=self.job, student=self.student_profile,
            proposal='Hired for payment test', status='hired',
        )
        Submission.objects.create(
            application=app,
            notes='All features implemented and tested.',
        )
        payment = Payment.objects.create(
            application=app, amount=Decimal('10000.00')
        )
        initial_earnings = self.student_profile.earnings

        response = self.client.get(
            reverse('company_release_payment', args=[payment.id])
        )
        self.assertRedirects(response, reverse('company_payments'))
        # Payment marked paid
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'paid',
            "Payment status must be 'paid' after release")
        self.assertIsNotNone(payment.paid_at,
            "paid_at timestamp must be set")
        # Student earnings credited
        self.student_profile.refresh_from_db()
        self.assertEqual(
            self.student_profile.earnings,
            Decimal(str(initial_earnings)) + Decimal('10000.00'),
            "Student earnings must be incremented by payment amount"
        )
        # Job marked completed
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, 'completed',
            "Job status must be 'completed' after payment release")


# ═════════════════════════════════════════════════════════════════════════════
# TC-UT-19 to TC-UT-20 — Admin Module
# ═════════════════════════════════════════════════════════════════════════════

class AdminModuleTests(TestCase):
    """Unit tests for admin_home and admin_toggle_student views."""

    def setUp(self):
        self.client = Client()
        self.admin_user = CustomUser.objects.create_user(
            username='admintest', password='TestPass@123', role='admin'
        )
        self.student_user, self.student_profile = make_student('adminstudent')
        _, _ = make_student('adminstudent2')   # second student for count test
        self.client.force_login(self.admin_user)

    # ── TC-UT-19 ──────────────────────────────────────────────────────────────
    def test_TC_UT_19_admin_dashboard_correct_student_count(self):
        """
        TC-UT-19 | admin_home — loads with accurate total_students count
        Input   : GET /admin-panel/ with 2 student profiles in DB
        Expected: HTTP 200, context['total_students'] == 2
        """
        response = self.client.get(reverse('admin_home'))
        self.assertEqual(response.status_code, 200,
            "Admin dashboard must return HTTP 200")
        self.assertIn('total_students', response.context,
            "'total_students' must be in template context")
        self.assertEqual(
            response.context['total_students'],
            StudentProfile.objects.count(),
            "total_students must match actual DB count"
        )

    # ── TC-UT-20 ──────────────────────────────────────────────────────────────
    def test_TC_UT_20_admin_toggle_student_active_status(self):
        """
        TC-UT-20 | admin_toggle_student — toggles is_active True → False → True
        Input   : GET /admin-panel/students/toggle/<user_id>/
        Expected: First call: is_active=False; Second call: is_active=True
        """
        self.assertTrue(self.student_user.is_active,
            "Student must be active before toggle")
        # First toggle: deactivate
        response = self.client.get(
            reverse('admin_toggle_student', args=[self.student_user.id])
        )
        self.assertRedirects(response, reverse('admin_manage_students'))
        self.student_user.refresh_from_db()
        self.assertFalse(self.student_user.is_active,
            "Student must be deactivated after first toggle")
        # Second toggle: reactivate
        self.client.get(
            reverse('admin_toggle_student', args=[self.student_user.id])
        )
        self.student_user.refresh_from_db()
        self.assertTrue(self.student_user.is_active,
            "Student must be reactivated after second toggle")

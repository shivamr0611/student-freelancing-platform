from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from .models import (
    CustomUser, StudentProfile, CompanyProfile,
    Job, Application, Submission, Payment, PlatformSettings
)
from .forms import (
    StudentRegistrationForm, CompanyRegistrationForm,
    JobPostForm, ApplicationForm, SubmissionForm,
    StudentProfileForm, CompanyProfileForm, PlatformSettingsForm
)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def role_required(role):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role != role:
                messages.error(request, "Access denied.")
                return redirect('login')
            return view_func(request, *args, **kwargs)
        wrapper.__name__ = view_func.__name__
        return wrapper
    return decorator


# ─── Auth Views ───────────────────────────────────────────────────────────────

def home_redirect(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.role == 'student':
        return redirect('student_home')
    elif request.user.role == 'company':
        return redirect('company_home')
    elif request.user.role == 'admin':
        return redirect('admin_home')
    return redirect('login')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home_redirect')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            if not user.is_active:
                messages.error(request, "Your account has been deactivated.")
                return render(request, 'auth/login.html')
            login(request, user)
            return redirect('home_redirect')
        messages.error(request, "Invalid username or password.")
    return render(request, 'auth/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    return render(request, 'auth/register_choice.html')


def register_student(request):
    form = StudentRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Welcome! Your student account is ready.")
        return redirect('student_home')
    return render(request, 'auth/register_student.html', {'form': form})


def register_company(request):
    form = CompanyRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Welcome! Your company account is ready.")
        return redirect('company_home')
    return render(request, 'auth/register_company.html', {'form': form})


# ─── Student Views ────────────────────────────────────────────────────────────

@role_required('student')
def student_home(request):
    profile = request.user.student_profile
    query = request.GET.get('q', '')
    skill_filter = request.GET.get('skill', '')
    budget_min = request.GET.get('budget_min', '')
    budget_max = request.GET.get('budget_max', '')
    deadline_filter = request.GET.get('deadline', '')

    jobs = Job.objects.filter(status='open').order_by('-created_at')

    if query:
        jobs = jobs.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if skill_filter:
        jobs = jobs.filter(required_skills__icontains=skill_filter)
    if budget_min:
        jobs = jobs.filter(budget__gte=budget_min)
    if budget_max:
        jobs = jobs.filter(budget__lte=budget_max)
    if deadline_filter:
        jobs = jobs.filter(deadline__lte=deadline_filter)

    applied_job_ids = Application.objects.filter(student=profile).values_list('job_id', flat=True)

    return render(request, 'student/home.html', {
        'jobs': jobs,
        'applied_job_ids': applied_job_ids,
        'profile': profile,
    })


@role_required('student')
def student_apply(request, job_id):
    profile = request.user.student_profile
    job = get_object_or_404(Job, id=job_id, status='open')

    if Application.objects.filter(job=job, student=profile).exists():
        messages.warning(request, "You already applied for this job.")
        return redirect('student_home')

    form = ApplicationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        app = form.save(commit=False)
        app.job = job
        app.student = profile
        app.save()
        messages.success(request, f"Applied for '{job.title}' successfully!")
        return redirect('student_applications')

    return render(request, 'student/apply.html', {'form': form, 'job': job})


@role_required('student')
def student_applications(request):
    profile = request.user.student_profile
    applications = Application.objects.filter(student=profile).select_related('job__company').order_by('-applied_at')
    return render(request, 'student/applications.html', {'applications': applications, 'profile': profile})


@role_required('student')
def student_active_jobs(request):
    profile = request.user.student_profile
    hired_apps = Application.objects.filter(student=profile, status='hired').select_related('job__company')
    return render(request, 'student/active_jobs.html', {'hired_apps': hired_apps, 'profile': profile})


@role_required('student')
def student_submit_work(request, app_id):
    profile = request.user.student_profile
    application = get_object_or_404(Application, id=app_id, student=profile, status='hired')

    existing = Submission.objects.filter(application=application).first()
    form = SubmissionForm(request.POST or None, request.FILES or None, instance=existing)

    if request.method == 'POST' and form.is_valid():
        sub = form.save(commit=False)
        sub.application = application
        sub.save()
        messages.success(request, "Work submitted successfully!")
        return redirect('student_active_jobs')

    return render(request, 'student/submit_work.html', {'form': form, 'application': application})


@role_required('student')
def student_profile(request):
    profile = request.user.student_profile
    form = StudentProfileForm(request.POST or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect('student_profile')
    payments = Payment.objects.filter(application__student=profile, status='paid')
    total_earnings = sum(p.amount for p in payments)
    return render(request, 'student/profile.html', {
        'form': form, 'profile': profile, 'total_earnings': total_earnings
    })


# ─── Company Views ────────────────────────────────────────────────────────────

@role_required('company')
def company_home(request):
    profile = request.user.company_profile
    jobs = Job.objects.filter(company=profile)
    total_jobs = jobs.count()
    active_jobs = jobs.filter(status='in_progress').count()
    total_applications = Application.objects.filter(job__company=profile).count()
    total_payments = Payment.objects.filter(application__job__company=profile, status='paid').count()
    recent_jobs = jobs.order_by('-created_at')[:5]
    return render(request, 'company/home.html', {
        'profile': profile,
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'total_applications': total_applications,
        'total_payments': total_payments,
        'recent_jobs': recent_jobs,
    })


@role_required('company')
def company_post_job(request):
    profile = request.user.company_profile
    form = JobPostForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        job = form.save(commit=False)
        job.company = profile
        job.save()
        messages.success(request, f"Job '{job.title}' posted successfully!")
        return redirect('company_home')
    return render(request, 'company/post_job.html', {'form': form, 'profile': profile})


@role_required('company')
def company_applicants(request):
    profile = request.user.company_profile
    job_id = request.GET.get('job')
    jobs = Job.objects.filter(company=profile)
    applications = Application.objects.filter(job__company=profile).select_related('student', 'job')
    if job_id:
        applications = applications.filter(job_id=job_id)
    return render(request, 'company/applicants.html', {
        'applications': applications, 'jobs': jobs, 'selected_job': job_id, 'profile': profile
    })


@role_required('company')
def company_hire(request, app_id):
    profile = request.user.company_profile
    application = get_object_or_404(Application, id=app_id, job__company=profile)
    application.status = 'hired'
    application.save()
    application.job.status = 'in_progress'
    application.job.save()
    # Reject other applicants for same job
    Application.objects.filter(job=application.job).exclude(id=app_id).update(status='rejected')
    # Create payment record
    Payment.objects.get_or_create(application=application, defaults={'amount': application.job.budget})
    messages.success(request, f"{application.student.full_name} has been hired!")
    return redirect('company_applicants')


@role_required('company')
def company_reject(request, app_id):
    profile = request.user.company_profile
    application = get_object_or_404(Application, id=app_id, job__company=profile)
    application.status = 'rejected'
    application.save()
    messages.info(request, "Application rejected.")
    return redirect('company_applicants')


@role_required('company')
def company_active_jobs(request):
    profile = request.user.company_profile
    active_jobs = Job.objects.filter(company=profile, status='in_progress').prefetch_related('applications')
    return render(request, 'company/active_jobs.html', {'active_jobs': active_jobs, 'profile': profile})


@role_required('company')
def company_payments(request):
    profile = request.user.company_profile
    payments = Payment.objects.filter(
        application__job__company=profile
    ).select_related('application__job', 'application__student').order_by('-created_at')
    return render(request, 'company/payments.html', {'payments': payments, 'profile': profile})


@role_required('company')
def company_release_payment(request, payment_id):
    profile = request.user.company_profile
    payment = get_object_or_404(Payment, id=payment_id, application__job__company=profile)
    payment.status = 'paid'
    payment.paid_at = timezone.now()
    payment.save()
    # Update student earnings
    student = payment.application.student
    student.earnings += payment.amount
    student.save()
    # Mark job as completed
    payment.application.job.status = 'completed'
    payment.application.job.save()
    messages.success(request, "Payment released successfully!")
    return redirect('company_payments')


@role_required('company')
def company_profile(request):
    profile = request.user.company_profile
    form = CompanyProfileForm(request.POST or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect('company_profile')
    return render(request, 'company/profile.html', {'form': form, 'profile': profile})


# ─── Admin Views ──────────────────────────────────────────────────────────────

@role_required('admin')
def admin_home(request):
    total_students = StudentProfile.objects.count()
    total_companies = CompanyProfile.objects.count()
    total_jobs = Job.objects.count()
    active_jobs = Job.objects.filter(status='in_progress').count()
    total_payments = Payment.objects.filter(status='paid').count()
    settings_obj = PlatformSettings.objects.first()
    commission = settings_obj.commission_rate if settings_obj else 10
    paid_total = sum(p.amount for p in Payment.objects.filter(status='paid'))
    platform_commission = paid_total * commission / 100

    return render(request, 'adminpanel/home.html', {
        'total_students': total_students,
        'total_companies': total_companies,
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'total_payments': total_payments,
        'platform_commission': platform_commission,
        'commission_rate': commission,
    })


@role_required('admin')
def admin_manage_students(request):
    students = StudentProfile.objects.select_related('user').order_by('-created_at')
    return render(request, 'adminpanel/manage_students.html', {'students': students})


@role_required('admin')
def admin_toggle_student(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, role='student')
    user.is_active = not user.is_active
    user.save()
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f"Student account {status}.")
    return redirect('admin_manage_students')


@role_required('admin')
def admin_manage_companies(request):
    companies = CompanyProfile.objects.select_related('user').order_by('-created_at')
    return render(request, 'adminpanel/manage_companies.html', {'companies': companies})


@role_required('admin')
def admin_toggle_company(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, role='company')
    user.is_active = not user.is_active
    user.save()
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f"Company account {status}.")
    return redirect('admin_manage_companies')


@role_required('admin')
def admin_settings(request):
    settings_obj, _ = PlatformSettings.objects.get_or_create(id=1)
    form = PlatformSettingsForm(request.POST or None, instance=settings_obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Platform settings updated.")
        return redirect('admin_settings')
    return render(request, 'adminpanel/settings.html', {'form': form})

from django.urls import path
from . import views

urlpatterns = [
    # ── Root ──────────────────────────────────────────────────────────────────
    path('', views.home_redirect, name='home_redirect'),

    # ── Auth ──────────────────────────────────────────────────────────────────
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('register/student/', views.register_student, name='register_student'),
    path('register/company/', views.register_company, name='register_company'),

    # ── Student ───────────────────────────────────────────────────────────────
    path('student/', views.student_home, name='student_home'),
    path('student/apply/<int:job_id>/', views.student_apply, name='student_apply'),
    path('student/applications/', views.student_applications, name='student_applications'),
    path('student/active-jobs/', views.student_active_jobs, name='student_active_jobs'),
    path('student/submit/<int:app_id>/', views.student_submit_work, name='student_submit_work'),
    path('student/profile/', views.student_profile, name='student_profile'),

    # ── Company ───────────────────────────────────────────────────────────────
    path('company/', views.company_home, name='company_home'),
    path('company/post-job/', views.company_post_job, name='company_post_job'),
    path('company/applicants/', views.company_applicants, name='company_applicants'),
    path('company/hire/<int:app_id>/', views.company_hire, name='company_hire'),
    path('company/reject/<int:app_id>/', views.company_reject, name='company_reject'),
    path('company/active-jobs/', views.company_active_jobs, name='company_active_jobs'),
    path('company/payments/', views.company_payments, name='company_payments'),
    path('company/release-payment/<int:payment_id>/', views.company_release_payment, name='company_release_payment'),
    path('company/profile/', views.company_profile, name='company_profile'),

    # ── Admin ─────────────────────────────────────────────────────────────────
    path('admin-panel/', views.admin_home, name='admin_home'),
    path('admin-panel/students/', views.admin_manage_students, name='admin_manage_students'),
    path('admin-panel/students/toggle/<int:user_id>/', views.admin_toggle_student, name='admin_toggle_student'),
    path('admin-panel/companies/', views.admin_manage_companies, name='admin_manage_companies'),
    path('admin-panel/companies/toggle/<int:user_id>/', views.admin_toggle_company, name='admin_toggle_company'),
    path('admin-panel/settings/', views.admin_settings, name='admin_settings'),
]

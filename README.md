# 🎓 Student Freelancing Platform

A full-stack Django web application with **3 roles**: Student, Company, Admin.

---

## 🗂️ Project Structure

```
student_freelancing/
├── manage.py
├── requirements.txt
├── student_freelancing/         ← Django project config
│   ├── settings.py              ← MySQL config here
│   ├── urls.py
│   └── wsgi.py
├── core/                        ← Single app (all logic here)
│   ├── models.py                ← 8 database models
│   ├── views.py                 ← All views for 3 dashboards
│   ├── urls.py                  ← All URL patterns
│   ├── forms.py                 ← All forms
│   └── admin.py
├── templates/
│   ├── base.html
│   ├── auth/                    ← login, register pages
│   ├── student/                 ← Student dashboard pages
│   ├── company/                 ← Company dashboard pages
│   └── adminpanel/              ← Admin panel pages
└── database/
    └── schema.sql               ← MySQL reference schema
```

---

## ⚡ Quick Setup (Step by Step)

### 1. Install Requirements

```bash
pip install -r requirements.txt
```
> Needs: Python 3.9+, MySQL Server running

### 2. Create MySQL Database

Open MySQL and run:
```sql
CREATE DATABASE student_freelancing_db CHARACTER SET utf8mb4;
```

### 3. Configure settings.py

Edit `student_freelancing/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'student_freelancing_db',
        'USER': 'root',          # ← your MySQL username
        'PASSWORD': '',          # ← your MySQL password
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### 4. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Admin User

```bash
python manage.py shell
```
Then in the shell:
```python
from core.models import CustomUser
u = CustomUser.objects.create_superuser(username='admin', password='admin123', email='admin@site.com')
u.role = 'admin'
u.save()
exit()
```

### 6. Run the Server

```bash
python manage.py runserver
```

Visit: **http://127.0.0.1:8000**

---

## 🌐 All URLs

| URL | Description |
|-----|-------------|
| `/login/` | Login page |
| `/register/` | Register choice page |
| `/register/student/` | Student registration |
| `/register/company/` | Company registration |
| `/student/` | Student dashboard (browse jobs) |
| `/student/applications/` | Student's applications |
| `/student/active-jobs/` | Hired jobs + submit work |
| `/student/profile/` | Edit student profile |
| `/company/` | Company dashboard |
| `/company/post-job/` | Post a job |
| `/company/applicants/` | Review & hire applicants |
| `/company/active-jobs/` | Monitor in-progress jobs |
| `/company/payments/` | Release payments |
| `/admin-panel/` | Admin overview |
| `/admin-panel/students/` | Manage students |
| `/admin-panel/companies/` | Manage companies |
| `/admin-panel/settings/` | Platform settings |
| `/django-admin/` | Django built-in admin |

---

## 👤 Roles & Features

### 🎓 Student
- Register / login
- Browse & filter jobs (search, skill, budget, deadline)
- Apply with a proposal
- Track application status (Pending / Hired / Rejected)
- Submit work (file + notes) for hired jobs
- View payment status
- Edit profile & view total earnings

### 🏢 Company
- Register / login
- Post jobs (title, description, skills, budget, deadline, category)
- Review all applicants and their proposals
- Hire one applicant (auto-rejects others)
- Monitor active/in-progress jobs
- Release payment when satisfied with submission
- Edit company profile

### 🔐 Admin
- Login (create via shell or Django admin)
- Platform overview (students, companies, jobs, payments, commission)
- Activate / deactivate student accounts
- Activate / deactivate company accounts
- Set platform commission rate
- Edit platform rules

---

## 🗄️ Database Models

| Model | Fields |
|-------|--------|
| `CustomUser` | username, password, role (student/company/admin), is_active |
| `StudentProfile` | full_name, email, college, skills, bio, phone, earnings |
| `CompanyProfile` | company_name, email, industry, website, description, phone |
| `Job` | title, description, required_skills, budget, deadline, status, category |
| `Application` | job, student, proposal, status (pending/hired/rejected) |
| `Submission` | application, file, notes |
| `Payment` | application, amount, status (not_paid/paid), paid_at |
| `PlatformSettings` | commission_rate, platform_rules |

---

## 📝 Notes

- `mysqlclient` requires MySQL dev headers: `sudo apt install libmysqlclient-dev` (Linux)
- On Windows with XAMPP/WAMP: just set USER/PASSWORD in settings.py
- Uploaded files stored in `media/submissions/`
- The `database/schema.sql` is for reference. Use `python manage.py migrate` to create tables.

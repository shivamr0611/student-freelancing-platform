from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('company', 'Company'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    college = models.CharField(max_length=300)
    skills = models.TextField(help_text="Comma-separated skills")
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

    def skills_list(self):
        return [s.strip() for s in self.skills.split(',') if s.strip()]


class CompanyProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='company_profile')
    company_name = models.CharField(max_length=300)
    email = models.EmailField()
    industry = models.CharField(max_length=200, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name


class Job(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('closed', 'Closed'),
    ]
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=300)
    description = models.TextField()
    required_skills = models.TextField(help_text="Comma-separated skills")
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    deadline = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    category = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def skills_list(self):
        return [s.strip() for s in self.required_skills.split(',') if s.strip()]


class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected'),
    ]
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='applications')
    proposal = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('job', 'student')

    def __str__(self):
        return f"{self.student.full_name} → {self.job.title}"


class Submission(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='submission')
    file = models.FileField(upload_to='submissions/', blank=True, null=True)
    notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Submission for {self.application}"


class Payment(models.Model):
    STATUS_CHOICES = [
        ('not_paid', 'Not Paid'),
        ('paid', 'Paid'),
    ]
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_paid')
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.status} — {self.application}"


class PlatformSettings(models.Model):
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00,
                                          help_text="Commission percentage (e.g. 10 = 10%)")
    platform_rules = models.TextField(blank=True, default="Standard platform rules apply.")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Platform Settings"
        verbose_name_plural = "Platform Settings"

    def __str__(self):
        return f"Platform Settings (Commission: {self.commission_rate}%)"

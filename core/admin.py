from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, StudentProfile, CompanyProfile, Job, Application, Submission, Payment, PlatformSettings

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_active']
    list_filter = ['role', 'is_active']
    fieldsets = UserAdmin.fieldsets + (('Role', {'fields': ('role',)}),)

admin.site.register(StudentProfile)
admin.site.register(CompanyProfile)
admin.site.register(Job)
admin.site.register(Application)
admin.site.register(Submission)
admin.site.register(Payment)
admin.site.register(PlatformSettings)

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, StudentProfile, CompanyProfile, Job, Application, Submission, PlatformSettings


class StudentRegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=200)
    email = forms.EmailField()
    college = forms.CharField(max_length=300)
    skills = forms.CharField(help_text="Enter skills separated by commas")
    phone = forms.CharField(max_length=15, required=False)
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name'],
                email=self.cleaned_data['email'],
                college=self.cleaned_data['college'],
                skills=self.cleaned_data['skills'],
                phone=self.cleaned_data.get('phone', ''),
                bio=self.cleaned_data.get('bio', ''),
            )
        return user


class CompanyRegistrationForm(UserCreationForm):
    company_name = forms.CharField(max_length=300)
    email = forms.EmailField()
    industry = forms.CharField(max_length=200, required=False)
    website = forms.URLField(required=False)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    phone = forms.CharField(max_length=15, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'company'
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            CompanyProfile.objects.create(
                user=user,
                company_name=self.cleaned_data['company_name'],
                email=self.cleaned_data['email'],
                industry=self.cleaned_data.get('industry', ''),
                website=self.cleaned_data.get('website', ''),
                description=self.cleaned_data.get('description', ''),
                phone=self.cleaned_data.get('phone', ''),
            )
        return user


class JobPostForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description', 'required_skills', 'budget', 'deadline', 'category']
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'required_skills': forms.TextInput(attrs={'placeholder': 'e.g. Python, Django, MySQL'}),
        }


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['proposal']
        widgets = {
            'proposal': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe why you are a good fit...'}),
        }


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['file', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['full_name', 'email', 'college', 'skills', 'bio', 'phone']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'skills': forms.TextInput(attrs={'placeholder': 'e.g. Python, Design, Writing'}),
        }


class CompanyProfileForm(forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = ['company_name', 'email', 'industry', 'website', 'description', 'phone']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class PlatformSettingsForm(forms.ModelForm):
    class Meta:
        model = PlatformSettings
        fields = ['commission_rate', 'platform_rules']
        widgets = {
            'platform_rules': forms.Textarea(attrs={'rows': 5}),
        }

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


User = get_user_model()

class Resume(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='resumes/resume')
    extracted_text = models.TextField(null=True)
    token_size = models.BigIntegerField(null=True)
    Choices = {
        '0' : 'Uploaded',
        '1' : 'Processing',
        '2': 'Done',
        '5': 'Failed',
        '7': 'Deleted'
    }
    status = models.CharField(max_length=1, choices=Choices, db_default='0')

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)


class parsed_data(models.Model):
    resume_id = models.OneToOneField(Resume, on_delete=models.CASCADE)
    fullname = models.CharField(max_length=355, null=True)
    emails = models.JSONField(default=dict, null=True)
    phones = models.JSONField(default=dict, null=True)
    skills = models.JSONField(default=dict, null=True)
    education = models.JSONField(default=dict, null=True)
    experience_years = models.FloatField(null=True)
    summary_text = models.TextField(null=True)
    keywords = models.JSONField(default=dict, null=True)
    tag = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
# Create your models here.

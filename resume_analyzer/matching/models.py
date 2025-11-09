from django.db import models
from django.contrib.auth import get_user_model
from resumes.models import Resume
from jobs.models import JobListing
from django.utils import timezone

# Create your models here.
class MatchResult(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE)
    match_score = models.FloatField(null=True)
    details = models.JSONField(default=dict, null=True)
    statusChoices = {
        '0': 'Inactive',
        '1': 'Active',
        '5': 'Deleted'
    }
    status = models.CharField(max_length=1, choices=statusChoices, db_default='1')
    created_at = models.DateTimeField(default=timezone.now)


class SavedJobs(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
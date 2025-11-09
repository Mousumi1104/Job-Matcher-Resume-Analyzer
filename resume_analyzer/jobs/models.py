from django.db import models


# Create your models here.
class JobListing(models.Model):
    statusChoices = {
        '0': 'Inactive',
        '1': 'Active',
        '5': 'Deleted'
    }
    title = models.CharField(max_length=255)
    j_id = models.TextField(unique=True, null=True)
    company = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    experience_year = models.CharField(max_length=100, null=True, blank=True)
    skills = models.JSONField(default=list)
    source = models.TextField(null=True)
    source_url = models.TextField(null=True, blank=True)
    apply_url = models.TextField(null=True, blank=True)
    remote = models.BooleanField(default=False)
    salary = models.CharField(max_length=255, null=True, blank=True)
    date_posted = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=1, choices=statusChoices, default='1')
    scraped_at = models.DateTimeField(auto_now_add=True)

    

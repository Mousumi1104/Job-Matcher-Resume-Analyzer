from django.db import models
from django.contrib.auth import get_user_model
from resumes.models import Resume
from jobs.models import JobListing
from django.utils import timezone
# Create your models here.
class Notification(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    resume = models.ForeignKey(Resume,on_delete=models.CASCADE)
    message = models.TextField(null=True)
    is_read =  models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
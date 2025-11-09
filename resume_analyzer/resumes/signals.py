from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Resume
from .tasks import parse_resume_task

@receiver(post_save, sender=Resume)
def trigger_resume_parsing(sender, instance, created, **kwargs):
    if created:
        # When a resume is uploaded, trigger background task
        parse_resume_task.delay(instance.id)

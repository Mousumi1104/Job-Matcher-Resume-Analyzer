from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Resume
from .tasks import parse_resume_task

@receiver(post_save, sender=Resume)
def trigger_resume_parsing(sender, instance, created, **kwargs):
    if created:
        # When a resume is uploaded, trigger background task
        # Enqueue only after the row is committed, so the worker can always find it
        transaction.on_commit(lambda: parse_resume_task.delay(instance.id))

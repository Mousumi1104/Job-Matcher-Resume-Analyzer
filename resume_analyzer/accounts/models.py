from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager 
from django.utils import timezone

# Create your models here.

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        else:
            email = self.normalize_email(email)
            user = self.model(email=email, **extra_fields)
            user.set_password(password)
            user.save(using=self._db)
            return user
        
    def create_superuser(self,email,password=None, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        return self.create_user(email, password, **extra_fields)



class Accounts(AbstractBaseUser):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    statusChoices = {
        '0': 'Inactive',
        '1': 'Active',
        '5': 'Deleted'
    }
    
    is_admin = models.BooleanField(db_default=False)
    experience_years = models.FloatField(null=True)
    status = models.CharField(max_length=1, choices=statusChoices, default='1')
    added_date = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['first_name', 'last_name']





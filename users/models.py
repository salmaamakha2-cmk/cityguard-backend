from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('citizen', 'Citizen'),
        ('admin', 'Admin'),
        ('technician', 'Technician'),
    )

    LANGUAGE_CHOICES = (
        ('fr', 'Français'),
        ('ar', 'العربية'),
        ('en', 'English'),
    )

    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    fcm_token = models.CharField(max_length=255, blank=True, null=True)
    preferred_language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='fr')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.role})"
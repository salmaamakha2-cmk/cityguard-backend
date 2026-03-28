from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Report(models.Model):
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('in_progress', 'En cours'),
        ('resolved', 'Résolu'),
        ('urgent', 'Urgent'),
    )
    SEVERITY_CHOICES = (
        ('low', 'Faible'),
        ('medium', 'Modéré'),
        ('high', 'Grave'),
    )
    CATEGORY_CHOICES = (
        ('pothole', 'Nid de poule'),
        ('lighting', 'Éclairage'),
        ('waste', 'Déchets'),
        ('water', 'Fuite eau'),
        ('other', 'Autre'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    technician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_reports')
    category_type = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='low')
    priority = models.IntegerField(default=1)
    is_critical = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    image = models.ImageField(upload_to='reports/', blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    quartier = models.CharField(max_length=100, blank=True)
    ai_analysis = models.JSONField(blank=True, null=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.status}"


class InterventionHistory(models.Model):
    ACTION_TYPE_CHOICES = (
        ('creation', 'Création'),
        ('affectation', 'Affectation'),
        ('changement_status', 'Changement de statut'),
        ('resolution', 'Résolution'),
    )

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='interventions')
    technician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPE_CHOICES, default='changement_status')
    note = models.TextField(blank=True)
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.report} - {self.action}"


class Notification(models.Model):
    TYPE_CHOICES = (
        ('status_update', 'Status Update'),
        ('new_report', 'New Report'),
        ('alert', 'Alert'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.user.username}"


class SystemSettings(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key
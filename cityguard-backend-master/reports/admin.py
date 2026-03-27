from django.contrib import admin
from .models import Report, Category, InterventionHistory, Notification, SystemSettings

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'category_type', 'status', 'severity', 'is_critical', 'user', 'created_at')
    list_filter = ('status', 'severity', 'category_type', 'is_critical')
    search_fields = ('title', 'description', 'quartier')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(InterventionHistory)
class InterventionHistoryAdmin(admin.ModelAdmin):
    list_display = ('report', 'technician', 'action', 'old_status', 'new_status', 'created_at')
    list_filter = ('new_status',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'is_read', 'created_at')
    list_filter = ('type', 'is_read')

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'updated_at')
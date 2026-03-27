from django.urls import path
from .views import (
    ReportListCreateView, ReportDetailView, ReportArchiveView,
    CategoryListCreateView, CategoryDetailView,
    InterventionCreateView,
    NotificationListView, NotificationMarkReadView,
    StatisticsView,
    ExportCSVView, ExportPDFView,
    SystemSettingsView, SystemSettingsDetailView,
    # AI
    AIAnalyzeView,
    AIAnalyzeTextView,
    AIAnalyzeImageView,
    AIAnalyzeFullView,
    ChatbotView,
)

urlpatterns = [
    # ── Reports ────────────────────────────────────────
    path('', ReportListCreateView.as_view(), name='reports-list'),
    path('<int:pk>/', ReportDetailView.as_view(), name='report-detail'),
    path('<int:pk>/archive/', ReportArchiveView.as_view(), name='report-archive'),

    # ── Categories ─────────────────────────────────────
    path('categories/', CategoryListCreateView.as_view(), name='categories-list'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),

    # ── Interventions ──────────────────────────────────
    path('interventions/', InterventionCreateView.as_view(), name='intervention-create'),

    # ── Notifications ──────────────────────────────────
    path('notifications/', NotificationListView.as_view(), name='notifications-list'),
    path('notifications/<int:pk>/', NotificationMarkReadView.as_view(), name='notification-detail'),

    # ── Statistics ─────────────────────────────────────
    path('statistics/', StatisticsView.as_view(), name='statistics'),

    # ── Export ─────────────────────────────────────────
    path('export/csv/', ExportCSVView.as_view(), name='export-csv'),
    path('export/pdf/', ExportPDFView.as_view(), name='export-pdf'),

    # ── Settings ───────────────────────────────────────
    path('settings/', SystemSettingsView.as_view(), name='settings-list'),
    path('settings/<int:pk>/', SystemSettingsDetailView.as_view(), name='settings-detail'),

    # ── AI ─────────────────────────────────────────────
    path('ai/analyze/', AIAnalyzeFullView.as_view(), name='ai-analyze-full'),
    path('ai/analyze-text/', AIAnalyzeTextView.as_view(), name='ai-analyze-text'),
    path('ai/analyze-image/', AIAnalyzeImageView.as_view(), name='ai-analyze-image'),
    path('ai/chatbot/', ChatbotView.as_view(), name='ai-chatbot'),
]
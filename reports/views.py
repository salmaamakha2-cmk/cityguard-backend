from rest_framework import generics, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from io import BytesIO
import csv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import datetime
from .models import Report, Category, InterventionHistory, Notification, SystemSettings
from .serializers import (ReportSerializer, CategorySerializer,
    InterventionHistorySerializer, NotificationSerializer,
    SystemSettingsSerializer, StatisticsSerializer)
from .ai_service import (
    analyze_report_text,
    analyze_report_image,
    analyze_full_report,
    chatbot_response,
)
from .firebase_service import send_notification_to_user


class IsAdminOrTechnician(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['admin', 'technician']


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'admin'


# ─── REPORTS ───────────────────────────────────────────
class ReportListCreateView(generics.ListCreateAPIView):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'category_type', 'status', 'quartier']
    ordering_fields = ['created_at', 'priority', 'severity']

    def get_queryset(self):
        user = self.request.user
        qs = Report.objects.all() if user.role == 'admin' else Report.objects.filter(user=user)
        qs = qs.filter(is_archived=False)

        status_f = self.request.query_params.get('status')
        severity_f = self.request.query_params.get('severity')
        category_f = self.request.query_params.get('category_type')
        quartier_f = self.request.query_params.get('quartier')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        critical_f = self.request.query_params.get('is_critical')

        if status_f: qs = qs.filter(status=status_f)
        if severity_f: qs = qs.filter(severity=severity_f)
        if category_f: qs = qs.filter(category_type=category_f)
        if quartier_f: qs = qs.filter(quartier__icontains=quartier_f)
        if date_from: qs = qs.filter(created_at__date__gte=date_from)
        if date_to: qs = qs.filter(created_at__date__lte=date_to)
        if critical_f: qs = qs.filter(is_critical=critical_f.lower() == 'true')

        return qs.order_by('-created_at')

    def perform_create(self, serializer):
        report = serializer.save(user=self.request.user)
        if report.severity == 'high':
            report.is_critical = True
            report.save()
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admins = User.objects.filter(role='admin')
        for admin in admins:
            Notification.objects.create(
                user=admin,
                report=report,
                type='new_report',
                message=f'Nouveau signalement: {report.title}'
            )
            send_notification_to_user(
                admin,
                title="🚨 Nouveau Signalement",
                body=f"{report.title} - {report.get_severity_display()}",
                report_id=report.id
            )


class ReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'technician']:
            return Report.objects.all()
        return Report.objects.filter(user=user)

    def perform_update(self, serializer):
        old = self.get_object()
        old_status = old.status
        report = serializer.save()
        if old_status != report.status:
            # Auto set resolved_at when status becomes resolved
            if report.status == 'resolved' and not report.resolved_at:
                report.resolved_at = datetime.datetime.now()
                report.save()
            InterventionHistory.objects.create(
                report=report,
                technician=self.request.user,
                action=f'Statut changé: {old_status} → {report.status}',
                action_type='changement_status',
                old_status=old_status,
                new_status=report.status
            )
            Notification.objects.create(
                user=report.user,
                report=report,
                type='status_update',
                message=f'Votre signalement "{report.title}" est maintenant: {report.get_status_display()}'
            )
            send_notification_to_user(
                report.user,
                title="📋 Statut mis à jour",
                body=f'Votre signalement est maintenant: {report.get_status_display()}',
                report_id=report.id
            )


# ─── ARCHIVE ───────────────────────────────────────────
class ReportArchiveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            report = Report.objects.get(pk=pk)
            report.is_archived = True
            report.save()
            return Response({'status': 'archived'})
        except Report.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)


# ─── CATEGORIES ────────────────────────────────────────
class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


# ─── INTERVENTIONS ─────────────────────────────────────
class InterventionCreateView(generics.CreateAPIView):
    serializer_class = InterventionHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(technician=self.request.user)


# ─── NOTIFICATIONS ─────────────────────────────────────
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')


class NotificationMarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            notif = Notification.objects.get(pk=pk, user=request.user)
            notif.is_read = True
            notif.save()
            return Response({'status': 'marked as read'})
        except Notification.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            notif = Notification.objects.get(pk=pk, user=request.user)
            notif.delete()
            return Response({'status': 'deleted'})
        except Notification.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)


# ─── STATISTICS ────────────────────────────────────────
class StatisticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = Report.objects.filter(is_archived=False)
        by_category = dict(qs.values_list('category_type').annotate(count=Count('id')))
        by_severity = dict(qs.values_list('severity').annotate(count=Count('id')))
        data = {
            'total_reports': qs.count(),
            'pending': qs.filter(status='pending').count(),
            'in_progress': qs.filter(status='in_progress').count(),
            'resolved': qs.filter(status='resolved').count(),
            'urgent': qs.filter(status='urgent').count(),
            'critical': qs.filter(is_critical=True).count(),
            'by_category': by_category,
            'by_severity': by_severity,
        }
        return Response(data)


# ─── EXPORT CSV ────────────────────────────────────────
class ExportCSVView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reports.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Title', 'Category', 'Status', 'Severity', 'Priority', 'Quartier', 'Date'])
        for r in Report.objects.filter(is_archived=False).order_by('-created_at'):
            writer.writerow([r.id, r.title, r.category_type, r.status, r.severity, r.priority, r.quartier, r.created_at.strftime('%Y-%m-%d')])
        return response


# ─── EXPORT PDF ────────────────────────────────────────
class ExportPDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        elements.append(Paragraph("CityGuard - Rapport des Signalements", styles['Title']))
        elements.append(Paragraph(f"Généré le: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        data = [['ID', 'Titre', 'Catégorie', 'Statut', 'Gravité', 'Quartier', 'Date']]
        for r in Report.objects.filter(is_archived=False).order_by('-created_at'):
            data.append([str(r.id), r.title[:30], r.category_type, r.status, r.severity, r.quartier, r.created_at.strftime('%Y-%m-%d')])
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0D47A1')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F5F5F5')]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="cityguard_reports.pdf"'
        return response


# ─── SYSTEM SETTINGS ───────────────────────────────────
class SystemSettingsView(generics.ListCreateAPIView):
    queryset = SystemSettings.objects.all()
    serializer_class = SystemSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]


class SystemSettingsDetailView(generics.RetrieveUpdateAPIView):
    queryset = SystemSettings.objects.all()
    serializer_class = SystemSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]


# ─── AI ANALYZE TEXT ───────────────────────────────────
class AIAnalyzeTextView(APIView):
    """
    Analyze report title + description using Gemini AI.
    Returns: category, severity, is_critical, is_urgent,
             suggested_title, improved_description, summary, confidence_score
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        title = request.data.get('title', '')
        description = request.data.get('description', '')
        language = request.data.get('language', 'fr')
        report_id = request.data.get('report_id', None)

        if not title and not description:
            return Response(
                {'error': 'title or description required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = analyze_report_text(title, description, language)

        # Save to report if report_id provided
        if report_id:
            try:
                report = Report.objects.get(id=report_id, user=request.user)
                report.ai_analysis = result
                if result.get('severity'):
                    report.severity = result['severity']
                if result.get('is_critical'):
                    report.is_critical = True
                if result.get('category') and result['category'] != 'other':
                    report.category_type = result['category']
                report.save()
                result['saved_to_report'] = report_id
            except Report.DoesNotExist:
                pass

        return Response(result)


# ─── AI ANALYZE IMAGE ──────────────────────────────────
class AIAnalyzeImageView(APIView):
    """
    Analyze report image using Gemini Vision AI.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        image_url = request.data.get('image_url', None)
        use_real = request.data.get('use_real_model', False)
        report_id = request.data.get('report_id', None)

        result = analyze_report_image(image_url, use_real_model=use_real)

        if report_id:
            try:
                report = Report.objects.get(id=report_id, user=request.user)
                report.ai_analysis = result
                if result.get('severity'):
                    report.severity = result['severity']
                if result.get('severity') == 'high':
                    report.is_critical = True
                report.save()
                result['saved_to_report'] = report_id
            except Report.DoesNotExist:
                pass

        return Response(result)


# ─── AI ANALYZE FULL (text + image) ────────────────────
class AIAnalyzeFullView(APIView):
    """
    Analyze both text and image together for a complete AI analysis.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        title = request.data.get('title', '')
        description = request.data.get('description', '')
        image_url = request.data.get('image_url', None)
        language = request.data.get('language', 'fr')
        report_id = request.data.get('report_id', None)

        if not title and not description:
            return Response(
                {'error': 'title or description required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = analyze_full_report(title, description, image_url, language)

        if report_id:
            try:
                report = Report.objects.get(id=report_id, user=request.user)
                report.ai_analysis = result
                if result.get('severity'):
                    report.severity = result['severity']
                if result.get('is_critical'):
                    report.is_critical = True
                if result.get('category') and result['category'] != 'other':
                    report.category_type = result['category']
                report.save()
                result['saved_to_report'] = report_id
            except Report.DoesNotExist:
                pass

        return Response(result)


# ─── CHATBOT ───────────────────────────────────────────
class ChatbotView(APIView):
    """
    CityGuard AI Chatbot powered by Gemini.
    Helps citizens create reports and understand the platform.

    Request body:
    {
        "message": "Je veux signaler un problème",
        "history": [
            {"role": "user", "parts": ["Bonjour"]},
            {"role": "model", "parts": ["Bonjour! Comment puis-je vous aider?"]}
        ],
        "language": "fr"
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        message = request.data.get('message', '')
        history = request.data.get('history', [])
        language = request.data.get('language', 'fr')

        if not message:
            return Response(
                {'error': 'message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = chatbot_response(message, history, language)
        return Response(result)


# ─── AI ANALYZE (legacy - kept for compatibility) ───────
class AIAnalyzeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        image_url = request.data.get('image_url', None)
        use_real = request.data.get('use_real_model', False)
        report_id = request.data.get('report_id', None)
        result = analyze_report_image(image_url, use_real_model=use_real)
        if report_id:
            try:
                report = Report.objects.get(id=report_id, user=request.user)
                report.ai_analysis = result
                if result.get('severity'):
                    report.severity = result['severity']
                if result.get('severity') == 'high':
                    report.is_critical = True
                report.save()
            except Report.DoesNotExist:
                pass
        return Response(result)
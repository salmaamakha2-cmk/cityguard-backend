from rest_framework import serializers
from .models import Report, Category, InterventionHistory, Notification, SystemSettings

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class InterventionHistorySerializer(serializers.ModelSerializer):
    technician_name = serializers.CharField(source='technician.username', read_only=True)
    class Meta:
        model = InterventionHistory
        fields = '__all__'

class ReportSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    technician_name = serializers.CharField(source='technician.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    interventions = InterventionHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if not ret.get('user_username'):
            ret['user_username'] = "Anonyme"
        return ret

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('user', 'created_at')

class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = '__all__'

class StatisticsSerializer(serializers.Serializer):
    total_reports = serializers.IntegerField()
    pending = serializers.IntegerField()
    in_progress = serializers.IntegerField()
    resolved = serializers.IntegerField()
    urgent = serializers.IntegerField()
    critical = serializers.IntegerField()
    by_category = serializers.DictField()
    by_severity = serializers.DictField()
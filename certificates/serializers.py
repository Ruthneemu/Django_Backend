# certificates/serializers.py
from rest_framework import serializers
from .models import Certificate
import time

class CertificateSerializer(serializers.ModelSerializer):
    # Add a serialized timestamp field for issue_date
    issue_date_timestamp = serializers.SerializerMethodField()
    
    class Meta:
        model = Certificate
        fields = '__all__'
    
    def get_issue_date_timestamp(self, obj):
        """Convert the issue_date to a Unix timestamp"""
        try:
            return int(obj.issue_date.timestamp())
        except (AttributeError, ValueError, TypeError):
            return None

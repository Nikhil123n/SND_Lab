from rest_framework import serializers # type: ignore
from .models import Job

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'step_ids', 'pipeline_json', 'created_at', 'status']


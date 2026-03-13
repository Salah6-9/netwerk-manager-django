from rest_framework import serializers
from monitoring.models import DeviceMetric
class MetricsSerializer(serializers.ModelSerializer):
    
    cpu_usage = serializers.FloatField()
    ram_usage = serializers.FloatField()
    disk_usage = serializers.FloatField()

    network_in = serializers.FloatField()
    network_out = serializers.FloatField()

    cpu_temperature = serializers.FloatField(required=False, allow_null=True)

    uptime = serializers.IntegerField()

    class Meta:
        model = DeviceMetric
        fields = [
            "cpu_usage",
            "ram_usage",
            "disk_usage",
            "network_in",
            "network_out",
            "cpu_temperature",
            "uptime",
        ]
    
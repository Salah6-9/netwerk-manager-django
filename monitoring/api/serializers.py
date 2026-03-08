from rest_framework import serializers

class MetricsSerializer(serializers.Serializer):
    
    cpu_usage = serializers.FloatField()
    ram_usage = serializers.FloatField()
    disk_usage = serializers.FloatField()

    network_in = serializers.FloatField()
    network_out = serializers.FloatField()

    cpu_temperature = serializers.FloatField(required=False, allow_null=True)

    uptime = serializers.IntegerField()

    
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from devices.models import Device
from monitoring.models import DeviceMetric, DeviceStatus

from .serializers import MetricsSerializer


class MetricsIngestView(APIView):

    authentication_classes = []
    permission_classes = []

    def post(self, request):

        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Agent "):
            return Response(
                {"error": "Missing agent token"},
                status=status.HTTP_403_FORBIDDEN
            )

        token = auth_header.split()[1]

        try:
            device = Device.objects.get(agent_token=token)
        except Device.DoesNotExist:
            return Response(
                {"error": "Invalid token"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = MetricsSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data

        # create history metric
        DeviceMetric.objects.create(
            device=device,
            **data
        )

        # update realtime status
        DeviceStatus.objects.update_or_create(
            device=device,
            defaults=data
        )

        return Response({"status": "ok"})
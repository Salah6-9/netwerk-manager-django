from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from devices.models import Device
from monitoring.models import DeviceMetric, DeviceStatus, DeviceEnrollmentRequest
from monitoring.alerts import check_device_alerts
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

        try:
            token = auth_header.split()[1]
        except IndexError:
            return Response(
                {"error": "Invalid Authorization header"},
                status=status.HTTP_403_FORBIDDEN
            )
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
        metric = serializer.save(device=device)

        # update realtime status
        DeviceStatus.objects.update_or_create(
            device=device,
            defaults=data
        )

        # Update heartbeat and recalculate status
        from django.utils import timezone
        device.last_agent_heartbeat = timezone.now()
        device.update_status()

        # check alerts
        check_device_alerts(device)

        return Response({"status": "ok"})

class DeviceEnrollmentView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):

        mac = request.data.get("mac")

        if not mac:
            return Response(
                {"error": "MAC address required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # check existing enrollment
        enrollment = DeviceEnrollmentRequest.objects.filter(mac=mac).first()

        if enrollment:

            if enrollment.status == "approved":

                device = Device.objects.filter(mac=mac).first()

                if not device:
                    # device was deleted but enrollment exists
                    enrollment.status = "pending"
                    enrollment.save()

                    return Response({
                        "status": "pending"
                    })

                return Response({
                    "status": "approved",
                    "agent_token": device.agent_token
                })

            return Response({
                "status": enrollment.status
            })

        # create new request
        enrollment = DeviceEnrollmentRequest.objects.create(
            user=request.user,   
            mac=mac,
            ip=request.data.get("ip"),
            hostname=request.data.get("hostname"),
            os=request.data.get("os"),
            agent_version=request.data.get("agent_version"),
        )

        return Response({
            "status": "pending"
        })
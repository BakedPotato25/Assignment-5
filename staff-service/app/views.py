from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Staff
from .serializers import StaffSerializer


class StaffListCreate(APIView):
    def get(self, request):
        return Response(StaffSerializer(Staff.objects.all(), many=True).data)

    def post(self, request):
        s = StaffSerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

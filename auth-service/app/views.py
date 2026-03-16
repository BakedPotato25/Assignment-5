import datetime
import os

import jwt
from django.contrib.auth import authenticate
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import RoleProfile
from .serializers import LoginSerializer, RegisterSerializer, TokenValidateSerializer
from . import metrics


def _jwt_secret():
    return os.environ.get("JWT_SECRET", "bookstore-jwt-dev-secret")


def _jwt_exp_hours():
    return int(os.environ.get("JWT_EXPIRE_HOURS", "12"))


def _build_token(user, role):
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": role,
        "iat": now,
        "exp": now + datetime.timedelta(hours=_jwt_exp_hours()),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


class RegisterView(APIView):
    def post(self, request):
        metrics.increment("auth_register_total")
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        role = user.role_profile.role if hasattr(user, "role_profile") else "customer"
        token = _build_token(user, role)
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": role,
                "access_token": token,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    def post(self, request):
        metrics.increment("auth_login_total")
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]
        user = authenticate(username=username, password=password)
        if not user:
            return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        role_profile, _ = RoleProfile.objects.get_or_create(user=user, defaults={"role": "customer"})
        token = _build_token(user, role_profile.role)

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": role_profile.role,
                "access_token": token,
            },
            status=status.HTTP_200_OK,
        )


class ValidateTokenView(APIView):
    def post(self, request):
        metrics.increment("auth_validate_total")
        serializer = TokenValidateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data["token"]
        try:
            payload = jwt.decode(token, _jwt_secret(), algorithms=["HS256"])
            metrics.increment("auth_validate_success_total")
            return Response({"valid": True, "payload": payload}, status=status.HTTP_200_OK)
        except jwt.ExpiredSignatureError:
            return Response({"valid": False, "error": "Token expired."}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return Response({"valid": False, "error": "Invalid token."}, status=status.HTTP_401_UNAUTHORIZED)


class HealthView(APIView):
    def get(self, request):
        return Response({"status": "ok", "service": "auth-service"}, status=status.HTTP_200_OK)


class MetricsView(APIView):
    def get(self, request):
        return HttpResponse(metrics.to_prometheus(), content_type="text/plain; version=0.0.4")

from typing import Any

from django.contrib.auth import login, logout
from requests import delete
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.templatetags.rest_framework import data

from todolist.core.models import User
from todolist.core.serializers import CreateUserSerializer, LoginSerializer, ProfileSerializer, UpdatePasswordSerializer


class SignupView(generics.CreateAPIView):
    serializer_class = CreateUserSerializer


class LoginView(generics.CreateAPIView):
    serializer_class = LoginSerializer

    def create(self, request: {data}, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_create(self, serializer) -> None:
        login(request=self.request, user=serializer.save())

class ProfileView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> Any:
        return self.request.user

    def perform_destroy(self, instance: {delete}) -> Response:
        logout(self.request)
        return Response(status=status.HTTP_204_NO_CONTENT)

class UpdatePasswordView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UpdatePasswordSerializer

    def get_object(self) -> Any:
        return self.request.user






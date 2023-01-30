from django.contrib.auth import login, logout
from rest_framework import generics, status
from rest_framework.response import Response

from todolist.core.serializers import CreateUserSerializer, LoginSerializer


class SignupView(generics.CreateAPIView):
    serializer_class = CreateUserSerializer


class LoginView(generics.CreateAPIView):
    serializer_class = LoginSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        login(request=self.request, user=serializer.save())



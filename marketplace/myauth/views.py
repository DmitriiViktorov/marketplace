import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated

from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView

from .utils import resize_image
from .models import Profile
from .serializers import (
    ProfileSerializer,
    UserRegistrationSerializer,
    UserPasswordChangeSerializer,
)


class RegisterView(CreateAPIView):
    """
    View to register a new user.
    """
    model = User
    fields = ['username', 'password']
    serializer_class = UserRegistrationSerializer

    def perform_create(self, serializer: UserRegistrationSerializer) -> None:
        """
         Perform the creation of a new user and authenticate them.

         :param serializer: Serializer instance with validated data
         """
        user = serializer.save()
        authenticate(self.request, username=user.username, password=user.password)
        login(self.request, user=user)

    def create(self, request: Request, *args, **kwargs) -> Response:
        """
        Create a new user.

        :param request: HTTP request
        :return: HTTP response
        """
        if not request.data.get('username'):
            data_string = list(request.data.keys())[0]
            data_dict = json.loads(data_string)
        else:
            data_dict = request.data
        serializer = self.get_serializer(data=data_dict)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(status=status.HTTP_200_OK)


class LoginView(APIView):
    """
    View to log in a user.
    """

    def post(self, request: Request, *args, **kwargs) -> Response:
        """
         Handle user login.

         :param request: HTTP request
         :return: HTTP response
         """
        if request.data.get('username'):
            username = request.data.get('username')
            password = request.data.get('password')
        else:
            data_string = list(request.data.keys())[0]
            data_dict = json.loads(data_string)
            username = data_dict.get('username')
            password = data_dict.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(APIView):
    """
    View to log out a user.
    """
    def post(self, request: Request) -> Response:
        """
        Handle user logout.

        :param request: HTTP request
        :return: HTTP response
        """
        logout(request)
        return Response(status=status.HTTP_200_OK)


class ProfileDetailView(LoginRequiredMixin, APIView):
    """
    View to retrieve and update user profile details.
    """
    def get(self, request: Request, *args, **kwargs) -> Response:
        """
          Retrieve user profile details.

          :param request: HTTP request
          :return: HTTP response
          """
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            profile = Profile.objects.get(user=request.user)
            serializer = ProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response(
                {"detail": "Profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Update user profile details.

        :param request: HTTP request
        :return: HTTP response
        """
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return Response(
                {"detail": "Profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = ProfileSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class AvatarUploadView(LoginRequiredMixin, APIView):
    """
    View to handle user avatar upload.
    """
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Handle avatar upload.

        :param request: HTTP request
        :return: HTTP response
        """
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return Response(
                {"detail": "Profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        avatar = request.FILES.get('avatar')

        if not avatar:
            return Response(
                {"detail": "Avatar file not provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        resized_avatar = resize_image(avatar)

        profile = Profile.objects.get(user=request.user)
        profile.src = resized_avatar
        profile.save()

        return Response(
            {"detail": "Avatar uploaded successfully."},
            status=status.HTTP_200_OK
        )


class PasswordChangeView(APIView):
    """
     View to handle user password change.
     """
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Handle password change.

        :param request: HTTP request
        :return: HTTP response
        """
        serializer = UserPasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():

            old_password = serializer.validated_data.get('currentPassword')
            user = authenticate(username=request.user.username, password=old_password)

            if user is None:
                return Response(
                    {"detail": "Incorrect current password."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            new_password = serializer.validated_data.get('newPassword')

            if len(new_password) < 6:
                return Response(
                    {"detail": "Password must be at least 6 characters."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            request.user.set_password(new_password)
            request.user.save()

            user = authenticate(username=request.user.username, password=new_password)
            if user is not None:
                login(request, user)
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(
                    {"detail": "Error logging in with the new password."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

from rest_framework import serializers
from .models import Profile
from django.contrib.auth.models import User


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the Profile model, including a custom method field for the avatar.
    """
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ('fullName', 'email', 'phone', 'avatar')

    def get_avatar(self, obj):
        """
        Get the avatar details for the profile.

        :param obj: Profile instance
        :return: Dictionary containing the avatar URL and alt text
        """
        return {
            "src": obj.src.url if obj.src else None,
            "alt": obj.alt
        }


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration, including the user's full name.
    """
    name = serializers.CharField(max_length=100, write_only=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'name')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        """
        Create a new user and their associated profile.

        :param validated_data: Validated data containing the username, password, and full name
        :return: Created User instance
        """
        full_name = validated_data.pop('name')
        user = User.objects.create_user(**validated_data)
        Profile.objects.create(user=user, fullName=full_name)
        return user


class UserPasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing the user's password.
    """

    currentPassword = serializers.CharField(max_length=128, write_only=True)
    newPassword = serializers.CharField(max_length=128, write_only=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

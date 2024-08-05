from django.db import models
from django.contrib.auth.models import User


def profile_avatar_directory_path(instance: "Profile", filename: str) -> str:
    """
    Generate the directory path for the profile avatar image.

    :param instance: Profile instance
    :param filename: Original filename of the uploaded image
    :return: String representing the file path where the avatar will be stored
    """
    return f"profiles/profile_{instance.pk}/avatar/{filename}"


class Profile(models.Model):
    """
    Model representing a user profile.

    Attributes:
        user (User): One-to-one relationship with the User model.
        fullName (str): Full name of the profile owner.
        email (str, optional): Email address of the profile owner.
        phone (str, optional): Phone number of the profile owner.
        src (ImageField, optional): Avatar image of the profile.
        alt (str): Alternative text for the avatar image.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fullName = models.CharField(max_length=100)
    email = models.EmailField(null=True, blank=True, unique=True)
    phone = models.CharField(max_length=12, null=True, blank=True, unique=True)
    src = models.ImageField(null=True, blank=True, upload_to=profile_avatar_directory_path)
    alt = models.CharField(max_length=100)



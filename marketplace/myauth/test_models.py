import os

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .models import Profile


class ProfileModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='testuser',
            password='<PASSWORD>',
        )
        cls.image_path = 'myauth/test_images/default_image.png'
        with open(cls.image_path, 'rb') as image_file:
            cls.uploaded_image = SimpleUploadedFile(
                name='user_avatar.png',
                content=image_file.read(),
                content_type='image/png'
            )

    def test_profile_creation(self):
        profile = Profile.objects.create(
            user=self.user,
            fullName='testuser full name',
            email='<EMAIL>',
            phone='1234567890',
        )
        self.assertEqual(profile.fullName, 'testuser full name')
        self.assertEqual(profile.email, '<EMAIL>')
        self.assertEqual(profile.phone, '1234567890')

    def test_profile_update(self):
        profile = Profile.objects.create(
            user=self.user,
            fullName='testuser full name',
            email='<EMAIL>',
            phone='1234567890',
        )
        profile.src = self.uploaded_image
        profile.alt = "test profile avatar"
        profile.save()
        self.assertEqual(profile.alt, "test profile avatar")
        self.assertEqual(profile.src, "profiles/profile_1/avatar/user_avatar.png")

    def test_profile_long_fullname(self):
        with self.assertRaises(ValidationError):
            profile = Profile.objects.create(
                user=self.user,
                fullName='A' * 101,
            )
            profile.full_clean()

    def test_profile_unique_email_phone(self):
        profile = Profile.objects.create(
            user=self.user,
            fullName='testuser full name',
            email='test@example.com',
            phone='1234567890',
        )
        another_user = User.objects.create_user(username='another_user', password='<PASSWORD>')
        with self.assertRaises(ValidationError):
            profile = Profile(
                user=another_user,
                fullName='another user full name',
                email='test@example.com',
                phone='0987654321',
            )
            profile.full_clean()

        with self.assertRaises(ValidationError):
            profile = Profile(
                user=another_user,
                fullName='another user full name',
                email='test-user@example.com',
                phone='1234567890',
            )
            profile.full_clean()

    def test_profile_long_alt(self):
        with self.assertRaises(ValidationError):
            profile = Profile.objects.create(
                user=self.user,
                alt='A' * 101,
            )
            profile.full_clean()

    def tearDown(self):
        for profile_avatar in Profile.objects.all():
            if profile_avatar.src:
                if os.path.isfile(profile_avatar.src.path):
                    os.remove(profile_avatar.src.path)

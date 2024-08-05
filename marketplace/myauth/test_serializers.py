import os

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from rest_framework.test import APITestCase

from .serializers import ProfileSerializer, UserRegistrationSerializer, UserPasswordChangeSerializer
from .models import Profile


class ProfileSerializerTestCase(APITestCase):
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
        cls.profile = Profile.objects.create(
            user=cls.user,
            fullName='testuser full name',
            email='<EMAIL>',
            phone='1234567890',
        )

    def test_get_and_update_profile(self):
        serializer = ProfileSerializer(self.profile)
        data = serializer.data
        expected_data = {
            'fullName': 'testuser full name',
            'email': '<EMAIL>',
            'phone': '1234567890',
            'avatar': {
                'src': None,
                "alt": ""
            }
        }
        self.assertEqual(data, expected_data)
        self.profile.src = self.uploaded_image
        self.profile.alt = 'test user avatar'
        self.profile.save()
        new_expected_data = {
            'fullName': 'testuser full name',
            'email': '<EMAIL>',
            'phone': '1234567890',
            'avatar': {
                'src': "/media/profiles/profile_1/avatar/user_avatar.png",
                "alt": "test user avatar"
            }
        }
        serializer = ProfileSerializer(self.profile)
        new_data = serializer.data
        self.assertEqual(new_data, new_expected_data)

    def test_create_profile(self):
        new_user = User.objects.create_user(username='testuser3', password='<PASSWORD>')
        data = {
            'fullName': 'Jane Doe',
            'email': 'jane@example.com',
            'phone': '9876543210'
        }
        serializer = ProfileSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        profile = serializer.save(user=new_user)
        self.assertEqual(profile.fullName, 'Jane Doe')
        self.assertEqual(profile.email, 'jane@example.com')
        self.assertEqual(profile.phone, '9876543210')

    def tearDown(self):
        for profile_avatar in Profile.objects.all():
            if profile_avatar.src:
                if os.path.isfile(profile_avatar.src.path):
                    os.remove(profile_avatar.src.path)


class UserRegistrationSerializerTestCase(APITestCase):
    def test_user_registration(self):
        data = {
            "username": "testuser4",
            "password": "<PASSWORD>",
            "name": 'full test profile username'
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        new_user = serializer.save()
        self.assertEqual(new_user.username, 'testuser4')
        profile = Profile.objects.get(user=new_user)
        self.assertEqual(profile.fullName, 'full test profile username')

    def test_user_wrong_username(self):
        data = {
            "username": "testuser4",
            "password": "<PASSWORD>",
            "name": "A" * 101
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)


class UserPasswordChangeSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='testuser',
            password='oldpassword123'
        )
        cls.valid_data = {
            'currentPassword': 'oldpassword123',
            'newPassword': 'newpassword456'
        }

    def test_valid_data(self):
        serializer = UserPasswordChangeSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_current_password(self):
        invalid_data = self.valid_data.copy()
        invalid_data['currentPassword'] = 'wrongpassword'
        serializer = UserPasswordChangeSerializer(data=invalid_data)
        self.assertTrue(serializer.is_valid())

    def test_empty_fields(self):
        empty_data = {
            'currentPassword': '',
            'newPassword': ''
        }
        serializer = UserPasswordChangeSerializer(data=empty_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('currentPassword', serializer.errors)
        self.assertIn('newPassword', serializer.errors)

import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from .models import Profile


class RegisterViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = "/api/sign-up"

    def test_register_view(self):
        data = {
            "username": "testuser4",
            "password": "<PASSWORD>",
            "name": 'full test profile username'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, None)
        self.assertTrue('_auth_user_id' in self.client.session)
        user_id = self.client.session['_auth_user_id']
        user = User.objects.get(id=user_id)
        self.assertEqual(user.username, "testuser4")
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.fullName, "full test profile username")

    def test_register_wrong_data(self):
        data = {
            "username": "testuser4",
            "password": "<PASSWORD>",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(response.data['name'][0], "This field is required.")


class LoginViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = "/api/sign-in"
        cls.user = User.objects.create_user(
            username="testuser4",
            email="<EMAIL>",
            password="<PASSWORD>"
        )
        cls.data = {"username": "testuser4", "password": "<PASSWORD>"}

    def test_login_view(self):
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, None)
        self.assertTrue('_auth_user_id' in self.client.session)
        user_id = self.client.session['_auth_user_id']
        user = User.objects.get(id=user_id)
        self.assertEqual(user.username, "testuser4")

    def test_login_wrong_data(self):
        data = {
            "username": "testuser4",
            "password": "<PASSWORDDD>",
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], "Invalid credentials.")


class LogoutViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.logout_url = "/api/sign-out"
        cls.user = User.objects.create_user(username="testuser4", email="<EMAIL>", password="<PASSWORD>")

    def test_logout_view(self):
        self.client.login(username="testuser4", password="<PASSWORD>")

        self.assertTrue('_auth_user_id' in self.client.session)

        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_logout_with_get_method(self):
        response = self.client.get(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class ProfileDetailViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.profile_url = "/api/profile"
        cls.login_url = "/sign-in/"
        cls.user = User.objects.create_user(
            username="testuser4",
            password="<PASSWORD>",
        )
        cls.profile = Profile.objects.create(
            user=cls.user,
            fullName="<NAME>",
            email="<EMAIL>",
            phone="0123456789",
        )

    def test_profile_detail_view(self):
        self.client.login(username="testuser4", password="<PASSWORD>")
        expected_data = {
            "fullName": "<NAME>",
            "email": "<EMAIL>",
            "phone": "0123456789",
            "avatar": {
                "src": None,
                "alt": ""
            }
        }
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)

    def test_profile_authenticated(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        expected_redirect_url = f'{self.login_url}?next={self.profile_url}'
        self.assertRedirects(response, expected_redirect_url)

    def test_missed_profile(self):
        new_user = User.objects.create_user(
            username="testuser5",
            password="<PASSWORD>",
        )
        self.client.login(username="testuser5", password="<PASSWORD>")
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], "Profile not found.")

    def test_profile_post_new_data(self):
        self.client.login(username="testuser4", password="<PASSWORD>")
        data = {
            "fullName": "New full name",
            "email": "new_email@example.com",
            "phone": "9876543210",
        }
        expected_data = {
            "fullName": "New full name",
            "email": "new_email@example.com",
            "phone": "9876543210",
            "avatar": {
                "src": None,
                "alt": ""
            }
        }
        response = self.client.post(self.profile_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.fullName, "New full name")
        self.assertEqual(self.profile.email, "new_email@example.com")
        self.assertEqual(self.profile.phone, "9876543210")

    def test_post_profile_authenticated(self):
        response = self.client.post(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        expected_redirect_url = f'{self.login_url}?next={self.profile_url}'
        self.assertRedirects(response, expected_redirect_url)

    def test_post_missed_profile(self):
        new_user = User.objects.create_user(
            username="testuser5",
            password="<PASSWORD>",
        )
        self.client.login(username="testuser5", password="<PASSWORD>")
        response = self.client.post(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], "Profile not found.")

    def test_post_profile_wrong_email(self):
        self.client.login(username="testuser4", password="<PASSWORD>")
        data = {
            "fullName": "New full name",
            "email": "--$$--",
            "phone": "9876543210",
        }
        response = self.client.post(self.profile_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['email'][0], "Enter a valid email address.")


class AvatarUploadViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.profile_url = "/api/profile/avatar"
        cls.login_url = "/sign-in/"
        cls.user = User.objects.create_user(
            username="testuser4",
            password="testpassword",
        )
        cls.profile = Profile.objects.create(
            user=cls.user,
            fullName="Test User",
            email="testuser@example.com",
            phone="0123456789",
        )
        cls.image_path = 'myauth/test_images/default_image.png'
        with open(cls.image_path, 'rb') as image_file:
            cls.uploaded_image = SimpleUploadedFile(
                name='user_avatar.png',
                content=image_file.read(),
                content_type='image/png'
            )

    def setUp(self):
        self.client = APIClient()

    def test_upload_avatar_successful(self):
        self.client.login(username="testuser4", password="testpassword")
        with open(self.image_path, 'rb') as image_file:
            response = self.client.post(
                self.profile_url,
                {'avatar': image_file},
                format='multipart'
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], "Avatar uploaded successfully.")

    def test_upload_avatar_without_authentication(self):
        with open(self.image_path, 'rb') as image_file:
            response = self.client.post(
                self.profile_url,
                {'avatar': image_file},
                format='multipart'
            )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        expected_redirect_url = f'{self.login_url}?next={self.profile_url}'
        self.assertRedirects(response, expected_redirect_url)

    def test_upload_avatar_without_file(self):
        self.client.login(username="testuser4", password="testpassword")
        response = self.client.post(self.profile_url, {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Avatar file not provided.")

    def test_upload_avatar_profile_not_found(self):
        self.profile.delete()
        self.client.login(username="testuser4", password="testpassword")
        with open(self.image_path, 'rb') as image_file:
            response = self.client.post(
                self.profile_url,
                {'avatar': image_file},
                format='multipart'
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], "Profile not found.")

    def tearDown(self):
        for profile in Profile.objects.all():
            if profile.src and os.path.isfile(profile.src.path):
                os.remove(profile.src.path)


class PasswordChangeViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password_change_url = "/api/profile/password"
        cls.user = User.objects.create_user(
            username="testuser4",
            password="oldpassword",
        )

    def setUp(self):
        self.client = APIClient()

    def test_password_change_successful(self):
        self.client.login(username="testuser4", password="oldpassword")
        response = self.client.post(self.password_change_url, {
            'currentPassword': 'oldpassword',
            'newPassword': 'newstrongpassword',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.logout()
        login_response = self.client.login(username="testuser4", password="newstrongpassword")
        self.assertTrue(login_response)

    def test_password_change_incorrect_current_password(self):
        self.client.login(username="testuser4", password="oldpassword")
        response = self.client.post(self.password_change_url, {
            'currentPassword': 'wrongpassword',
            'newPassword': 'newstrongpassword',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Incorrect current password.")

    def test_password_change_short_new_password(self):
        self.client.login(username="testuser4", password="oldpassword")
        response = self.client.post(self.password_change_url, {
            'currentPassword': 'oldpassword',
            'newPassword': 'short',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Password must be at least 6 characters.")

    def test_password_change_without_authentication(self):
        response = self.client.post(self.password_change_url, {
            'currentPassword': 'oldpassword',
            'newPassword': 'newstrongpassword',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], "Authentication credentials were not provided.")
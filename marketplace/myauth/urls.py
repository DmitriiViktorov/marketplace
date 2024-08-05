from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView,
    ProfileDetailView, AvatarUploadView, PasswordChangeView
)

app_name = 'myauth'

urlpatterns = [
    path("sign-in", LoginView.as_view(), name="sign-in"),
    path("sign-up", RegisterView.as_view(), name="sign-up"),
    path("sign-out", LogoutView.as_view(), name="sign-out"),

    path("profile", ProfileDetailView.as_view(), name="profile"),
    path("profile/password", PasswordChangeView.as_view(), name="avatar-upload"),
    path("profile/avatar", AvatarUploadView.as_view(), name="avatar-upload"),
]

from django.urls import path
from django.contrib.auth import views as auth_views

from . import views
urlpatterns = [

    path('login',views.login_view,name='login'),
    path('register',views.register,name='register'),
    path('', views.dashboard, name='dashboard'),
    path('logout', views.logout_view, name='logout'),

    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='accounts/change_password.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/change_password_done.html'), name='password_change_done'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='accounts/reset_password.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/reset_password_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/reset_password_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/reset_password_complete.html'), name='password_reset_complete'),
]
from django.urls import path
from django.contrib.auth import views as auth_views

from . import views
urlpatterns = [

    path('upload-resume',views.upload_resume,name='upload_resume'),
    path('resumes', views.resumes_list, name='resumes_list'),
    path('resumes-detail/<int:resume_id>', views.resume_detail, name='resume_detail'),
    path('delete-resume/<int:id>', views.delete_resume, name='delete_resume')
]
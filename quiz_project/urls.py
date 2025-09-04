"""quiz_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from core import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('category/<int:category_id>/', views.category_quizzes, name='category_quizzes'),
    path('quiz/<int:quiz_id>/start/', views.start_quiz, name='start_quiz'),
    # path('quiz/attempt/', views.attempt_quiz, name='attempt_quiz'),
    path('quiz/<int:quiz_id>/attempt/', views.attempt_quiz, name='attempt_quiz'),
    path('quiz/<int:quiz_id>/result/', views.quiz_result, name='quiz_result'),
    path('my-attempts/', views.my_attempts, name='my_attempts'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.admin_manage_users, name='admin_manage_users'),
    path('admin/users/add/', views.admin_add_user, name='admin_add_user'),
    path('admin/users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('admin/users/upload_csv/', views.upload_users_csv, name='upload_users_csv'),
    path('admin/users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('admin/quizzes/', views.admin_manage_quizzes, name='admin_manage_quizzes'),
    path('admin/quizzes/add/', views.admin_add_quiz, name='admin_add_quiz'),
    path('admin/quizzes/edit/<int:quiz_id>/', views.admin_edit_quiz, name='admin_edit_quiz'),
    path('admin/quizzes/delete/<int:quiz_id>/', views.admin_delete_quiz, name='admin_delete_quiz'),
    path('admin/quizzes/upload_csv/', views.upload_quizzes_csv, name='upload_quizzes_csv'),
    path('admin/quizzes/<int:quiz_id>/add-question/', views.admin_add_question, name='admin_add_question'),
    path('admin/upload-mcq/', views.upload_mcq_csv, name='upload_mcq_csv'),
    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('blogs/', views.blog_list, name='blog_list'),
    path('blogs/<int:blog_id>/', views.blog_detail, name='blog_detail'),
    path('about/', views.about_us, name='about'),
    path('contact/', views.contact, name='contact'),
    path('courses/', views.course, name='course'),
    path('categories/', views.category_list, name='category_list'),
    path('blogs/tag/<str:tag_name>/', views.blogs_by_tag, name='blogs_by_tag'),
    path('blogs/submit/', views.submit_blog, name='submit_blog'),
    path('blog/<int:blog_id>/react/<str:reaction_type>/', views.toggle_blog_reaction, name='blog_react'),

    path('admin/ckeditor/', include('ckeditor_uploader.urls')),
    path('admin/blogs/', views.admin_blogs, name='admin_blogs'),
    path('admin/blogs/add/', views.add_blog, name='add_blog'),
    path('admin/blogs/<int:blog_id>/edit/', views.edit_blog, name='edit_blog'),
    path('admin/blogs/<int:blog_id>/delete/', views.delete_blog, name='delete_blog'),

    # path('api/', include('api.urls')),

    path('search/', views.search, name='search'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from django.urls import path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from myproject import views
from .views import (
    post_list_create, post_detail, comment_list_create, comment_detail,
    like_post, unlike_post, create_comment, get_comments_for_post
)


# Swagger API Documentation
schema_view = get_schema_view(
    openapi.Info(
        title="Crime Backend API Documentation",
        default_version='v1',
        description="API documentation for Crime Backend project",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email=""),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Swagger UI
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('swagger.json/', schema_view.without_ui(cache_timeout=0), name='schema-json'),

    # Post URLs
    path('posts/', post_list_create, name='post-list-create'),  
    path('posts/<int:pk>/', post_detail, name='post-detail'),  

    # Like/Unlike URLs
    path('posts/<int:pk>/like/', like_post, name='like-post'),  # Like post
    path('posts/<int:pk>/unlike/', unlike_post, name='unlike-post'),  # Unlike post

    # Comment URLs
    # path('posts/<int:post_id>/comments/', comment_list_create, name='comment-list-create'),  
    path('comments/<int:pk>/', comment_detail, name='comment-detail'),  
   
    # Firebase Auth-based Comment Endpoints
    path('posts/<int:pk>/comment/', create_comment, name='create-comment'),
    path('posts/<int:pk>/comments-detail/', get_comments_for_post, name='get-comments-for-post'),

    # Add these new paths for email verification
    path('send-verification-code/', views.send_verification_email, name='send_verification_email'),
    path('check-verification-code/', views.check_verification_code, name='check_verification_code'),

    path('match/', views.match_suspect, name='match_suspect'),
    path('upload-suspect/', views.upload_suspect, name='upload_suspect'),
]


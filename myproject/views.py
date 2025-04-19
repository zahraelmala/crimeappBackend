# views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from .models import Post, Comment
from .serializers import PostSerializer, CommentSerializer
from django.conf import settings
from django.utils.crypto import get_random_string
from django.core.cache import cache
import random
from django.core.mail import send_mail

@swagger_auto_schema(
    method='post',
    request_body=PostSerializer,
    responses={201: PostSerializer}
)
@api_view(['GET', 'POST'])
def post_list_create(request):
    if request.method == 'GET':
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='put',
    request_body=PostSerializer,
    responses={200: PostSerializer}
)
@api_view(['GET', 'PUT', 'DELETE'])
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if request.method == 'GET':
        serializer = PostSerializer(post)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = PostSerializer(post, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        post.delete()
        return Response({'message': 'Post deleted successfully'}, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='post',
    request_body=CommentSerializer,
    responses={201: CommentSerializer, 400: "Bad Request", 404: "Post Not Found"},
)
@api_view(['GET', 'POST'])
def comment_list_create(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if request.method == 'GET':
        comments = Comment.objects.filter(post=post)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = CommentSerializer(data=request.data, context={'post': post})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='put',
    request_body=CommentSerializer,
    responses={200: CommentSerializer}
)
@api_view(['GET', 'PUT', 'DELETE'])
def comment_detail(request, pk):
    comment = get_object_or_404(Comment, pk=pk)

    if request.method == 'GET':
        serializer = CommentSerializer(comment)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = CommentSerializer(comment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        comment.delete()
        return Response({'message': 'Comment deleted successfully'}, status=status.HTTP_200_OK)
    

from .serializers import EmailVerificationSerializer
from sendgrid.helpers.mail import Mail, Email, To, Content
from django.conf import settings

from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Email, To, Content, Mail

# Method to send verification code to email
@swagger_auto_schema(
    method='post',
    request_body=EmailVerificationSerializer,
    responses={200: "Verification code sent", 400: "Bad Request"}
)
@api_view(['POST'])
def send_verification_email(request):
    # Validate and get the email from request body
    serializer = EmailVerificationSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data.get('email')
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate a random 4-digit verification code
    verification_code = '1234'  # Replace with your code generation logic

    # Store the verification code in cache with an expiration time (e.g., 5 minutes)
    cache.set(f'verification_code_{email}', verification_code, timeout=300)  # Timeout of 5 minutes

    # Prepare the email content
    subject = "Your Verification Code"
    message = f"Your verification code is {verification_code}. It will expire in 5 minutes."
    html_message = f"<html><body><h1>Your Verification Code</h1><p>Your verification code is <strong>{verification_code}</strong>. It will expire in 5 minutes.</p></body></html>"

    # Send the email using SendGrid
    try:
        sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        from_email = Email(settings.DEFAULT_FROM_EMAIL)
        to_email = To(email)
        content = Content("text/plain", message)
        mail = Mail(from_email, to_email, subject, content)
        mail.html = html_message  # Set the HTML message
        response = sg.send(mail)
        print(f"Email sent to {email} with status code {response.status_code}")
        return Response({"message": "Verification code sent"}, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error sending email: {e}")
        return Response({"error": "Failed to send verification email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Method to check the verification code
@swagger_auto_schema(
    method='post',
    request_body=EmailVerificationSerializer,
    responses={200: "Code verified", 400: "Invalid code", 404: "Code expired"}
)
@api_view(['POST'])
def check_verification_code(request):
    # Validate and get the email and code from request body
    serializer = EmailVerificationSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data.get('email')
        code = serializer.validated_data.get('code')  # Using the code from serializer
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Check if the code is provided
    if not code:
        return Response({"error": "Code is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Retrieve the stored verification code from cache
    stored_code = cache.get(f'verification_code_{email}')
    
    # Check if the code has expired or not found
    if not stored_code:
        return Response({"error": "Code expired or not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if the entered code matches the stored one
    if stored_code == code:
        return Response({"message": "Code verified successfully"}, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Invalid verification code"}, status=status.HTTP_400_BAD_REQUEST)

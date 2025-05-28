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
from firebase_admin import auth
from rest_framework import status
import logging
# Configure logger
logger = logging.getLogger(__name__)

# Utility function to get Firebase UID from the token
def get_user_from_token(id_token):
    try:
        # Log the token being verified
        logger.debug(f"Verifying ID token: {id_token}")
        decoded_token = auth.verify_id_token(id_token)
        logger.debug(f"Decoded token: {decoded_token}")
        return decoded_token['uid']
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return None

# Like a Post
@api_view(['POST'])
def like_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    logger.debug(f"Post found: {post}")

    # Get Firebase ID token from request headers
    id_token = request.headers.get('Authorization')
    logger.debug(f"Received ID token: {id_token}")

    if not id_token:
        logger.warning("Token is missing in the request")
        return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Clean the token if 'Bearer ' prefix is present
    if id_token.startswith('Bearer '):
        id_token = id_token[7:]
        logger.debug(f"Cleaned token: {id_token}")

    # Verify and get the user UID from Firebase
    user_uid = get_user_from_token(id_token)

    if not user_uid:
        logger.warning("Invalid or expired token")
        return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

    # Check if user is already in the list of likes
    if user_uid in post.likes:
        logger.info(f"User {user_uid} already liked the post.")
        return Response({"message": "You already liked this post"}, status=status.HTTP_400_BAD_REQUEST)

    # Add the user ID to the likes list
    post.likes.append(user_uid)
    post.save()
    logger.info(f"Post liked by user: {user_uid}")

    return Response({"message": "Post liked successfully"}, status=status.HTTP_200_OK)

# Unlike a Post
@api_view(['POST'])
def unlike_post(request, pk):
    post = get_object_or_404(Post, pk=pk)

    id_token = request.headers.get('Authorization')
    logger.debug(f"Received ID token: {id_token}")

    if not id_token:
        logger.warning("Token is missing in the request")
        return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Clean the token if 'Bearer ' prefix is present
    if id_token.startswith('Bearer '):
        id_token = id_token[7:]
        logger.debug(f"Cleaned token: {id_token}")

    # Verify and get the user UID from Firebase
    user_uid = get_user_from_token(id_token)

    if not user_uid:
        return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

    # Check if the user ID is in the likes list
    if user_uid not in post.likes:
        return Response({"message": "You haven't liked this post yet"}, status=status.HTTP_400_BAD_REQUEST)

    # Remove the user ID from the likes list
    post.likes.remove(user_uid)
    post.save()

    return Response({"message": "Post unliked successfully"}, status=status.HTTP_200_OK)

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
import os
from dotenv import load_dotenv

load_dotenv()  # Make sure this is at the top of settings.py

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")

# Utility function to generate a 4-digit code
def generate_verification_code():
    return str(random.randint(1000, 9999))


@swagger_auto_schema(
    method='post',
    request_body=EmailVerificationSerializer,
    responses={200: "Verification code sent", 400: "Bad Request"}
)
@api_view(['POST'])
def send_verification_email(request):
    serializer = EmailVerificationSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data.get('email')
    verification_code = generate_verification_code()

    # Store the code with a 5-minute expiry
    cache_key = f'verification_code_{email}'
    cache.set(cache_key, verification_code, timeout=300)

    subject = "Your Verification Code"
    plain_message = f"Your verification code is {verification_code}. It will expire in 5 minutes."
    html_message = f"""
    <html>
      <body>
        <h2>Your Verification Code</h2>
        <p>Your verification code is <strong>{verification_code}</strong>.</p>
        <p>This code will expire in 5 minutes.</p>
      </body>
    </html>
    """

    try:
        sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)
        mail = Mail(
            from_email=Email(DEFAULT_FROM_EMAIL),
            to_emails=To(email),
            subject=subject,
            plain_text_content=Content("text/plain", plain_message),
            html_content=html_message
        )
        response = sg.send(mail)
        print(f"Email sent to {email} - Status: {response.status_code}")
        return Response({"message": "Verification code sent"}, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"SendGrid error: {e}")
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
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data.get('email').lower().strip()
    code = serializer.validated_data.get('code', '').strip()

    # Check if the code is provided
    if not code:
        return Response({"error": "Code is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Retrieve the stored verification code from cache
    cache_key = f'verification_code_{email}'
    stored_code = cache.get(cache_key)

    # Debugging logs
    print(f"[DEBUG] Cache Key: {cache_key}")
    print(f"[DEBUG] Stored Code: {stored_code}")
    print(f"[DEBUG] Entered Code: {code}")

    # Check if the code has expired or not found
    if not stored_code:
        return Response({"error": "Code expired or not found"}, status=status.HTTP_404_NOT_FOUND)

    # Check if the entered code matches the stored one
    if stored_code == code:
        return Response({"message": "Code verified successfully"}, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Invalid verification code"}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    request_body=CommentSerializer,
    responses={201: CommentSerializer}
)
@api_view(['POST'])
def create_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)

    # Get token
    id_token = request.headers.get('Authorization')
    if not id_token:
        return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

    if id_token.startswith('Bearer '):
        id_token = id_token[7:]

    # Verify token
    user_uid = get_user_from_token(id_token)
    if not user_uid:
        return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

    # Create comment
    serializer = CommentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(post=post, firebase_uid=user_uid)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_comments_for_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.all().order_by('-created_at')
    serialized_comments = CommentSerializer(comments, many=True)

    response_data = {
        "post": {
            "post_id": post.post_id,
            "caption": post.caption,
            "likes": post.likes,
            "username": post.username,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "location": post.location,
            "post_pic": post.post_pic,
            "profile_pic": post.profile_pic,
        },
        "comments": serialized_comments.data
    }

    return Response(response_data, status=status.HTTP_200_OK)

import numpy as np
from django.http import JsonResponse
from deepface import DeepFace
from pymongo import MongoClient
import gridfs
import cv2
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from django.core.files.uploadedfile import InMemoryUploadedFile

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["Crime_Catcher"]
fs = gridfs.GridFS(db)

# Load encodings once
known_encodings = []
known_names = []

def load_known_faces():
    global known_encodings, known_names
    known_encodings.clear()
    known_names.clear()
    for stored_file in fs.find():
        file_data = stored_file.read()
        np_arr = np.frombuffer(file_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        try:
            embedding = DeepFace.represent(img, model_name="Facenet")[0]["embedding"]
            known_encodings.append(embedding)
            known_names.append(stored_file.filename)
        except Exception as e:
            print(f"Error processing {stored_file.filename}: {e}")
    print(f"Loaded {len(known_encodings)} suspect faces.")

# Load at startup
load_known_faces()

@csrf_exempt
@require_http_methods(["POST"])
def match_suspect(request):
    try:
        file = request.FILES.get('image')
        if not file:
            return JsonResponse({'error': 'No image provided'}, status=400)

        # Read uploaded image
        file_data = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(file_data, cv2.IMREAD_COLOR)

        # Extract embedding
        input_embedding = DeepFace.represent(img, model_name="Facenet")[0]["embedding"]

        for i, stored_embedding in enumerate(known_encodings):
            distance = np.linalg.norm(np.array(input_embedding) - np.array(stored_embedding))
            if distance < 10:
                return JsonResponse({'message': 'Match found', 'suspect': known_names[i]})

        return JsonResponse({'message': 'No match found'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def upload_suspect(request):
    try:
        file = request.FILES.get('image')
        name = request.POST.get('name', 'suspect_unknown.jpg')

        if not file:
            return JsonResponse({'error': 'No image provided'}, status=400)

        # Save to MongoDB GridFS
        file_id = fs.put(file, filename=name)
        print(f"Uploaded suspect {name} with ID {file_id}")

        # Reload encodings with new entry
        load_known_faces()

        return JsonResponse({'message': f'{name} uploaded and indexed'}, status=201)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


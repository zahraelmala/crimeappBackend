# views.py
import base64
from io import BytesIO
from tkinter import Image
import uuid
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

import os
import time
import threading
import numpy as np
import cv2
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from deepface import DeepFace
from pymongo import MongoClient
import gridfs
from PIL import Image
import uuid
import tempfile
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema

# --- MongoDB Connection ---
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["Crime_Catcher"]
fs = gridfs.GridFS(db)

# --- Globals for caching face data ---
known_faces = {}  # Cached embeddings grouped by suspect name
faces_loaded = False
SIMILARITY_THRESHOLD = 0.55  # Adjustable matching threshold


def cosine_similarity(a, b):
    """Compute cosine similarity between two vectors."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def load_known_faces():
    global known_faces
    print("🔄 Loading suspect faces from GridFS...")
    start = time.time()
    known_faces.clear()

    for stored_file in fs.find():
        file_data = stored_file.read()
        np_arr = np.frombuffer(file_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img is None:
            print(f"❌ Failed to decode image: {stored_file.filename}")
            continue

        try:
            result = DeepFace.represent(img, model_name="Facenet", enforce_detection=False)
            if not result or "embedding" not in result[0]:
                print(f"⚠️ No face detected in {stored_file.filename}")
                continue

            embedding = result[0]["embedding"]
            # Extract full base filename (without extension), keep timestamp
            base_name = stored_file.filename.rsplit('.', 1)[0]  # e.g. "suspect_1748478825"
            if base_name not in known_faces:
                known_faces[base_name] = []
            known_faces[base_name].append(embedding)
        except Exception as e:
            print(f"⚠️ Error processing {stored_file.filename}: {e}")

    total_embeddings = sum(len(v) for v in known_faces.values())
    print(f"✅ Loaded {total_embeddings} embeddings for {len(known_faces)} suspects in {time.time() - start:.2f}s")



def ensure_faces_loaded():
    """Load faces once if not already loaded."""
    global faces_loaded
    if not faces_loaded:
        load_known_faces()
        faces_loaded = True

def get_image_base64_from_gridfs(filename):
    try:
        file = fs.find_one({'filename': filename})
        if file:
            image_data = file.read()
            encoded = base64.b64encode(image_data).decode('utf-8')
            # Detect mime-type by file extension
            ext = filename.split('.')[-1].lower()
            mime = f"image/{'jpeg' if ext == 'jpg' else ext}"
            return f"data:{mime};base64,{encoded}"
        else:
            print(f"File not found in GridFS: {filename}")
    except Exception as e:
        print(f"Error reading GridFS file '{filename}': {e}")
    return None

def find_suspect_image_filename(base_name):
    print(f"Searching for base_name: {base_name}")
    for ext in ['jpg', 'png', 'jpeg']:
        filename = f"{base_name}.{ext}"
        print(f"Checking filename: {filename}")
        file = fs.find_one({'filename': filename})
        if file:
            print(f"Found file: {filename}")
            return filename
    print("No matching file found.")
    return None

@csrf_exempt
@swagger_auto_schema(
    method='post',
    request_body=None,
    responses={200: "Match found", 400: "Bad Request", 500: "Internal Server Error"}
)
@api_view(['POST'])
@require_http_methods(["POST"])
def match_suspect(request):
    input_embeddings = []

    # Ensure known faces cache is ready
    ensure_faces_loaded()

    # Handle uploaded image
    if 'image' in request.FILES:
        image_file = request.FILES['image']
        try:
            img_array = np.array(Image.open(image_file))
            result = DeepFace.represent(img_array, model_name='Facenet', enforce_detection=False)
            if result and 'embedding' in result[0]:
                input_embeddings.append(result[0]['embedding'])
            else:
                return JsonResponse({'match': False, 'message': 'No face detected in image'}, status=200)
        except Exception as e:
            return JsonResponse({'error': f'Image processing error: {str(e)}'}, status=500)

    # Handle uploaded video
    elif 'video' in request.FILES:
        video_file = request.FILES['video']
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}.mp4")
        try:
            with open(temp_path, 'wb') as f:
                for chunk in video_file.chunks():
                    f.write(chunk)

            cap = cv2.VideoCapture(temp_path)
            frames_checked = 0
            max_frames = 100
            frame_interval = 5  # Process every 5th frame to speed up

            while cap.isOpened() and frames_checked < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break

                if frames_checked % frame_interval == 0:
                    try:
                        result = DeepFace.represent(frame, model_name='Facenet', enforce_detection=False)
                        if result and 'embedding' in result[0]:
                            input_embeddings.append(result[0]['embedding'])
                        if len(input_embeddings) >= 3:
                            break
                    except Exception:
                        pass  # Ignore individual frame errors

                frames_checked += 1

            cap.release()
        except Exception as e:
            return JsonResponse({'error': f'Video processing error: {str(e)}'}, status=500)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    else:
        return JsonResponse({'error': 'No image or video uploaded'}, status=400)

    if not input_embeddings:
        return JsonResponse({'match': False, 'message': 'No face found in upload'}, status=200)

    if not known_faces:
        return JsonResponse({'match': False, 'message': 'No known suspects in database'}, status=200)

    # Find best match among cached embeddings
    best_similarity = 0
    best_match = None

    for input_emb in input_embeddings:
        for name, stored_embs in known_faces.items():
            for stored_emb in stored_embs:
                sim = cosine_similarity(np.array(input_emb), np.array(stored_emb))
                if sim > best_similarity:
                    best_similarity = sim
                    best_match = name

    if best_similarity > SIMILARITY_THRESHOLD:
        matched_filename = find_suspect_image_filename(best_match)
        matched_image_data = None
        print(f"Matched filename: {matched_filename}")
        if matched_filename:
            matched_image_data = get_image_base64_from_gridfs(matched_filename)
            print(f"Matched image data length: {len(matched_image_data) if matched_image_data else 'None'}")
        print(f"🔍 Best match: {best_match} with similarity {best_similarity:.2f}")
        print(f"Matched image data: {matched_image_data}")
        return JsonResponse({
            'match': True,
            'name': best_match,
            'confidence': round(best_similarity * 100, 2),
            'threshold': SIMILARITY_THRESHOLD * 100,
            'matched_face_url': matched_image_data,  # base64 string or None
        })
    else:
        return JsonResponse({
            'match': False,
            'confidence': round(best_similarity * 100, 2),
            'threshold': SIMILARITY_THRESHOLD * 100
        })


@csrf_exempt
def upload_suspect(request):
    try:
        file = request.FILES.get('media')  # 'media' can be image or video
        name = request.POST.get('name', 'suspect')

        if not file:
            return JsonResponse({'error': 'No media file provided'}, status=400)

        content_type = file.content_type
        timestamp = int(time.time())

        if 'image' in content_type:
            unique_name = f"{name}_{timestamp}.jpg"
            file_id = fs.put(file, filename=unique_name)
            print(f"🖼️ Uploaded suspect image: {unique_name} with ID {file_id}")

        elif 'video' in content_type:
            np_video = np.frombuffer(file.read(), np.uint8)
            video_temp = f"/tmp/{name}_{timestamp}.mp4"
            with open(video_temp, 'wb') as temp_file:
                temp_file.write(np_video)

            cap = cv2.VideoCapture(video_temp)
            success, frame = cap.read()
            face_saved = False

            while success:
                result = DeepFace.represent(frame, model_name="Facenet", enforce_detection=False)
                if result and "embedding" in result[0]:
                    _, encoded_img = cv2.imencode('.jpg', frame)
                    file_id = fs.put(encoded_img.tobytes(), filename=f"{name}_{timestamp}.jpg")
                    print(f"🎥 Extracted face frame saved for {name} from video, ID: {file_id}")
                    face_saved = True
                    break
                success, frame = cap.read()

            cap.release()
            os.remove(video_temp)

            if not face_saved:
                return JsonResponse({'error': 'No clear face detected in video'}, status=400)

        else:
            return JsonResponse({'error': 'Unsupported media type'}, status=400)

        # Reload faces cache asynchronously after upload
        def reload_faces_async():
            global faces_loaded
            try:
                load_known_faces()
                faces_loaded = True
            except Exception as e:
                print(f"⚠️ Error reloading faces: {e}")

        threading.Thread(target=reload_faces_async).start()

        return JsonResponse({'message': f'{name} uploaded and indexing started'}, status=201)

    except Exception as e:
        print(f"🚨 Upload error: {e}")
        return JsonResponse({'error': str(e)}, status=500)






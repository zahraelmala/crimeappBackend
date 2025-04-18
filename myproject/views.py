from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from .models import Post, Comment, CreatedBy
from .serializers import PostSerializer, CommentSerializer
from django.utils.timezone import now

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
        created_by_data = request.data.get('created_by')

        if created_by_data:
            try:
                created_by = CreatedBy.objects.get(id=created_by_data["id"])
            except CreatedBy.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            created_by = None  

        post_data = request.data.copy()
        post_data.pop('created_by', None)

        serializer = PostSerializer(data=post_data)
        if serializer.is_valid():
            serializer.save(created_by=created_by)
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
            post.caption = serializer.validated_data.get('caption', post.caption)
            post.location = serializer.validated_data.get('location', post.location)
            post.crimeTime = serializer.validated_data.get('crimeTime', post.crimeTime)
            post.crimeType = serializer.validated_data.get('crimeType', post.crimeType)
            post.post_pic = serializer.validated_data.get('post_pic', post.post_pic)
            post.likes = serializer.validated_data.get('likes', post.likes)
            post.updated_at = now()
            post.save()
            return Response(PostSerializer(post).data)
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
        commented_by = None
        commented_by_data = request.data.get('commented_by', None)
        if commented_by_data:
            commented_by = get_object_or_404(CreatedBy, id=commented_by_data["id"])
        
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            comment = Comment.objects.create(
                post=post,
                commented_by=commented_by,
                text=serializer.validated_data['text'],
                updated_at=now()
            )
            return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
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
            comment.text = serializer.validated_data.get('text', comment.text)
            comment.updated_at = now()
            comment.save()
            return Response(CommentSerializer(comment).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        comment.delete()
        return Response({'message': 'Comment deleted successfully'}, status=status.HTTP_200_OK)

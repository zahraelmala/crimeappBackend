from rest_framework import serializers
from .models import Post, Comment

class CreatedBySerializer(serializers.Serializer):
    userId = serializers.IntegerField()
    username = serializers.CharField(max_length=255)
    profilePic = serializers.CharField(max_length=500)

class PostSerializer(serializers.ModelSerializer):
    createdBy = CreatedBySerializer()
    
    class Meta:
        model = Post
        fields = ['id', 'createdBy', 'createdAt', 'updatedAt', 'postPic', 'likes']

class CommentSerializer(serializers.ModelSerializer):
    commentedBy = CreatedBySerializer()
    
    class Meta:
        model = Comment
        fields = ['id', 'post', 'commentedBy', 'createdAt', 'updatedAt', 'text']

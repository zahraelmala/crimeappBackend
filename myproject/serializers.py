from rest_framework import serializers
from .models import Post, Comment

class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    code = serializers.CharField(max_length=4, required=True)

class PostSerializer(serializers.ModelSerializer):

    class Meta:
        model = Post
        fields = ['post_id', 'caption', 'location', 'crimeTime', 'crimeType',
                   'username', 'profile_pic' , 
                   'post_pic', 'likes', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['comment_id', 'post', 'firebase_uid', 'text', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
{
  "caption": "test post 1",
  "location": "Sidi Gaber - Alexandria",
  "crimeTime": "Wed, 02 Apr 2025 at 4:34 AM",
  "crimeType": "Theft",
  "username": "john_doe",
  "profile_pic": "https://img.url/avatar.jpg",
  "post_pic": "https://yourpicurl.com/pic.jpg",
  "likes": 23
}

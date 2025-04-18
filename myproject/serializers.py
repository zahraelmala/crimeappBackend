from rest_framework import serializers
from .models import CreatedBy, Post, Comment, User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'profile_pic']

class CreatedBySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='user.id')
    username = serializers.CharField(source='user.username')
    profile_pic = serializers.CharField(source='user.profile_pic')

    class Meta:
        model = CreatedBy
        fields = ['id', 'username', 'profile_pic']

class PostSerializer(serializers.ModelSerializer):
    created_by = CreatedBySerializer(read_only=True)

    class Meta:
        model = Post
        fields = ['post_id', 'caption', 'location', 'crimeTime','crimeType','created_by', 'created_at', 'updated_at', 'post_pic', 'likes']
        read_only_fields = ['created_by', 'created_at', 'updated_at']

class CommentSerializer(serializers.ModelSerializer):
    commented_by = CreatedBySerializer(required=False)

    class Meta:
        model = Comment
        fields = ['comment_id', 'post', 'commented_by', 'created_at', 'updated_at', 'text']
        read_only_fields = ['created_at', 'updated_at']


{
  "caption": "test post 1",
  "location": "Sidi Gaber - Alexandria",
  "crimeTime": "Wed, 02 Apr 2025 at 4:34 AM",
  "crimeType": "Theft",
  "created_by": {
    "id": 1,
    "username": "Abdelrahman",
    "profile_pic": "https://firebasestorage.googleapis.com/v0/b/gog-web-13346.appspot.com/o/userPic%2F30.png?alt=media&token=3187c36e-7f11-421d-be27-8db64d843358"
  },
  "post_pic": "https://firebasestorage.googleapis.com/v0/b/gog-web-13346.appspot.com/o/userPic%2F30.png?alt=media&token=3187c36e-7f11-421d-be27-8db64d843358",
  "likes": 23
}
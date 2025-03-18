from django.db import models
from django.contrib.auth.models import User

class CreatedBy(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=255)
    user_profile_pic = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.username

class Post(models.Model):
    id = models.AutoField(primary_key=True)
    caption = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(CreatedBy, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    post_pic = models.URLField(blank=True, null=True)
    likes = models.IntegerField(default=0)

    def __str__(self):
        return f"Post {self.id} by {self.created_by.username}"

class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    commented_by = models.ForeignKey(CreatedBy, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    text = models.TextField()

    def __str__(self):
        return f"Comment {self.id} on Post {self.post.id} by {self.commented_by.username}"

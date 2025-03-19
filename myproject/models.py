from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser, Group, Permission

class User(AbstractUser):
    profile_pic = models.URLField(null=True, blank=True)  # Ensure correct field name

    # Avoid reverse accessor conflicts by setting unique related_name values
    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_groups",  # Custom related_name
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions",  # Custom related_name
        blank=True
    )

    def __str__(self):
        return self.username

class CreatedBy(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=255)
    user_profile_pic = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.username

class Post(models.Model):
    post_id = models.AutoField(primary_key=True)
    caption = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(CreatedBy, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    post_pic = models.URLField(blank=True, null=True)
    likes = models.IntegerField(default=0)

    def __str__(self):
        return f"Post {self.id} by {self.created_by.username}"

class Comment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    commented_by = models.ForeignKey(CreatedBy, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    text = models.TextField()

    def __str__(self):
        return f"Comment {self.id} on Post {self.post.id} by {self.commented_by.username}"

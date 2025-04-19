from django.db import models

class Post(models.Model):
    post_id = models.AutoField(primary_key=True)
    caption = models.TextField(blank=True, null=True)
    location = models.TextField(blank=True, null=True)
    crimeTime = models.TextField(blank=True, null=True)
    crimeType = models.TextField(blank=True, null=True)
    username = models.TextField(blank=True, null=True)
    profile_pic = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    post_pic = models.URLField(blank=True, null=True)
    likes = models.IntegerField(default=0)

    def __str__(self):
        return f"Post {self.post_id} by {self.username}"

class Comment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    comment_username = models.TextField(blank=True, null=True)  # Uncomment and add this
    comment_profile_pic = models.URLField(blank=True, null=True)  # Uncomment and add this
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Comment {self.comment_id} on Post {self.post.post_id} by {self.comment_username}"


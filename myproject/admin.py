from django.contrib import admin
from .models import Post, Comment

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1  

class PostAdmin(admin.ModelAdmin):
    list_display = ('post_id', 'caption', 
                    'username', 'profile_pic',
                      'created_at', 'updated_at')  
    list_filter = ('created_at', 'updated_at')

class CommentAdmin(admin.ModelAdmin):
    list_display = ('comment_id', 'text',
                      'created_at', 'updated_at')  
    list_filter = ('created_at', 'updated_at')

admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
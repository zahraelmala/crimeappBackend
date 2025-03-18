from django.contrib import admin
from .models import Post, Comment

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1  

class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'caption', 'created_by', 'created_at', 'updated_at')  
    list_filter = ('created_at', 'updated_at')

class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'commented_by', 'created_at', 'updated_at')  
    list_filter = ('created_at', 'updated_at')

admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
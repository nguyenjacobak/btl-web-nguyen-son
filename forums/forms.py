from django import forms
from .models import Comment, Forum

class ForumForm(forms.ModelForm):
    class Meta:
        model = Forum
        fields = ['title', 'desc']
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['desc']
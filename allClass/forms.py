# myClass/forms.py
from django import forms
from .models import MyClass
class ClassRequestForm(forms.Form):
    code = forms.CharField(max_length=10, label='Class Code')
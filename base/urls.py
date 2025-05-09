from django.urls import path
from . import views
from account.views import login as alogin
from .models import *
import json
urlpatterns = [
    path('',alogin,name='login'),
    path('welcome/',views.welcome,name='welcome'),
    path('not_support/',views.not_support,name='not_support'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('callback/', views.bling_callback, name='bling_callback'),
] 
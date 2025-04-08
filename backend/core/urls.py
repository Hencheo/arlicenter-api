from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('callback/', views.bling_callback, name='bling_callback'),
] 
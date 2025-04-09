from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('callback/', views.bling_callback, name='bling_callback'),
    path('api/token/', views.get_bling_token_info, name='get_bling_token_info'),
    path('api/produtos/', views.get_bling_produtos, name='get_bling_produtos'),
    path('api/pedidos/', views.get_bling_pedidos, name='get_bling_pedidos'),
    path('api/contatos/', views.get_bling_contatos, name='get_bling_contatos'),
    path('api/teste/cpf/', views.teste_busca_por_cpf, name='teste_busca_por_cpf'),
] 
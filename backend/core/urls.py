from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('callback/', views.bling_callback, name='bling_callback'),
    path('api/token/', views.get_bling_token_info, name='get_bling_token_info'),
    path('api/token/status/', views.check_token_status, name='check_token_status'),
    path('api/token/verify-expiration/', views.verify_token_expiration, name='verify_token_expiration'),
    path('api/token/run-expiration-check/', views.run_token_expiration_check, name='run_token_expiration_check'),
    path('api/tokens/delete-all/', views.delete_all_tokens, name='delete_all_tokens'),
    path('api/auth/generate-url/', views.generate_authorization_url, name='generate_authorization_url'),
    path('generate-auth-url/', views.generate_authorization_url, name='simple_generate_url'),
    path('api/produtos/', views.get_bling_produtos, name='get_bling_produtos'),
    path('api/pedidos/', views.get_bling_pedidos, name='get_bling_pedidos'),
    path('api/contatos/', views.get_bling_contatos, name='get_bling_contatos'),
    path('api/contatos/<str:id_contato>/', views.get_contato_by_id, name='get_contato_by_id'),
    path('api/teste/cpf/', views.teste_busca_por_cpf, name='teste_busca_por_cpf'),
    path('api/teste/cpf/completo/', views.teste_busca_por_cpf_completo, name='teste_busca_por_cpf_completo'),
    path('api/auth/login/', views.user_login, name='user_login'),
]
from django.urls import path
from . import views, views_supervision
from .google_auth import google_login_redirect, google_callback

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('supervision/', views_supervision.supervision_view, name='supervision'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('laravel-sso/', views.laravel_sso_login, name='laravel_sso_login'),
    # Google OAuth
    path('google/login/', google_login_redirect, name='google_login'),
    path('google/callback/', google_callback, name='google_callback'),
    path('oauth/choose-role/', views.oauth_choose_role_view, name='oauth_choose_role'),
    
    # Gestion des élèves par les admins
    path('admin/eleves/', views.admin_eleve_list_view, name='admin_eleve_list'),
    path('admin/eleves/create/', views.admin_eleve_create_view, name='admin_eleve_create'),
    path('admin/eleves/<uuid:user_id>/edit/', views.admin_eleve_edit_view, name='admin_eleve_edit'),
    path('admin/eleves/<uuid:user_id>/delete/', views.admin_eleve_delete_view, name='admin_eleve_delete'),
    path('admin/eleves/<uuid:user_id>/', views.admin_eleve_detail_view, name='admin_eleve_detail'),
]

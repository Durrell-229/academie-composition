from django.urls import path
from . import views, views_supervision, views_gestion
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

    # Gestion des utilisateurs (profs, conseillers, admins) par les admins
    path('admin/users/', views.admin_user_list_view, name='admin_user_list'),
    path('admin/users/create/', views.admin_user_create_view, name='admin_user_create'),
    path('admin/users/<uuid:user_id>/edit/', views.admin_user_edit_view, name='admin_user_edit'),
    path('admin/users/<uuid:user_id>/delete/', views.admin_user_delete_view, name='admin_user_delete'),

    # Actions gamification (admin)
    path('admin/grant-badge/', views.grant_badge_view, name='grant_badge'),
    path('admin/grant-xp/', views.grant_xp_view, name='grant_xp'),

    # ─── Actions rapides utilisateurs ─────────────────────────────
    path('admin/users/<uuid:user_id>/toggle/', views_gestion.admin_user_toggle_active, name='admin_user_toggle'),
    path('admin/users/<uuid:user_id>/role/', views_gestion.admin_user_change_role, name='admin_user_role'),
]

# ─── Hub gestion admin (monté sur /gestion/ dans urls principal) ───────────
from django.urls import include

gestion_urlpatterns = [
    path('', views_gestion.admin_hub, name='admin_hub'),
    path('classes-matieres/', views_gestion.admin_classes_matieres, name='admin_classes_matieres'),
    path('classes-matieres/classe/create/', views_gestion.admin_classe_save, name='admin_classe_create'),
    path('classes-matieres/classe/<int:classe_id>/edit/', views_gestion.admin_classe_save, name='admin_classe_edit'),
    path('classes-matieres/classe/<int:classe_id>/delete/', views_gestion.admin_classe_delete, name='admin_classe_delete'),
    path('classes-matieres/matiere/create/', views_gestion.admin_matiere_save, name='admin_matiere_create'),
    path('classes-matieres/matiere/<int:matiere_id>/edit/', views_gestion.admin_matiere_save, name='admin_matiere_edit'),
    path('classes-matieres/matiere/<int:matiere_id>/delete/', views_gestion.admin_matiere_delete, name='admin_matiere_delete'),
    path('approbations/', views_gestion.admin_approbations, name='admin_approbations'),
    path('approbations/exam/<uuid:exam_id>/', views_gestion.admin_approuver_exam, name='admin_approuver_exam'),
    path('approbations/cours/<int:cours_id>/', views_gestion.admin_approuver_cours, name='admin_approuver_cours'),
    path('annonces/', views_gestion.admin_annonces, name='admin_annonces'),
    path('annonces/create/', views_gestion.admin_annonce_save, name='admin_annonce_create'),
    path('annonces/<int:annonce_id>/edit/', views_gestion.admin_annonce_save, name='admin_annonce_edit'),
    path('annonces/<int:annonce_id>/delete/', views_gestion.admin_annonce_delete, name='admin_annonce_delete'),
    path('annonces/<int:annonce_id>/toggle/', views_gestion.admin_annonce_toggle, name='admin_annonce_toggle'),
    path('bourses/', views_gestion.admin_bourses, name='admin_bourses'),
    path('bourses/<uuid:bourse_id>/decision/', views_gestion.admin_bourse_decision, name='admin_bourse_decision'),
]

"""
URLs du hub de gestion admin — monté sur /gestion/ dans le projet principal.
"""
from django.urls import path
from . import views_gestion

app_name = 'gestion'

urlpatterns = [
    path('', views_gestion.admin_hub, name='hub'),

    # ── Classes & Matières ──────────────────────────────────────────
    path('classes-matieres/', views_gestion.admin_classes_matieres, name='classes_matieres'),
    path('classes-matieres/classe/create/', views_gestion.admin_classe_save, name='classe_create'),
    path('classes-matieres/classe/<uuid:classe_id>/edit/', views_gestion.admin_classe_save, name='classe_edit'),
    path('classes-matieres/classe/<uuid:classe_id>/delete/', views_gestion.admin_classe_delete, name='classe_delete'),
    path('classes-matieres/matiere/create/', views_gestion.admin_matiere_save, name='matiere_create'),
    path('classes-matieres/matiere/<uuid:matiere_id>/edit/', views_gestion.admin_matiere_save, name='matiere_edit'),
    path('classes-matieres/matiere/<uuid:matiere_id>/delete/', views_gestion.admin_matiere_delete, name='matiere_delete'),

    # ── Approbations ────────────────────────────────────────────────
    path('approbations/', views_gestion.admin_approbations, name='approbations'),
    path('approbations/exam/<uuid:exam_id>/', views_gestion.admin_approuver_exam, name='approuver_exam'),
    path('approbations/cours/<int:cours_id>/', views_gestion.admin_approuver_cours, name='approuver_cours'),

    # ── Annonces ────────────────────────────────────────────────────
    path('annonces/', views_gestion.admin_annonces, name='annonces'),
    path('annonces/create/', views_gestion.admin_annonce_save, name='annonce_create'),
    path('annonces/<int:annonce_id>/edit/', views_gestion.admin_annonce_save, name='annonce_edit'),
    path('annonces/<int:annonce_id>/delete/', views_gestion.admin_annonce_delete, name='annonce_delete'),
    path('annonces/<int:annonce_id>/toggle/', views_gestion.admin_annonce_toggle, name='annonce_toggle'),

    # ── Bourses ─────────────────────────────────────────────────────
    path('bourses/', views_gestion.admin_bourses, name='bourses'),
    path('bourses/<uuid:bourse_id>/decision/', views_gestion.admin_bourse_decision, name='bourse_decision'),

    # ── Actions utilisateurs ────────────────────────────────────────
    path('users/<uuid:user_id>/toggle/', views_gestion.admin_user_toggle_active, name='user_toggle'),
    path('users/<uuid:user_id>/role/', views_gestion.admin_user_change_role, name='user_role'),
]

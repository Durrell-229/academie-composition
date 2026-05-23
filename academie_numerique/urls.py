from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from core.views import home_view, admin_dashboard_view, promo_video_view

from core.api_urls import api as core_api
from api.v1.router import api as v1_api

urlpatterns = [
    path('', promo_video_view, name='promo'),
    path('accueil/', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('admin_dashboard/', admin_dashboard_view, name='admin_dashboard'),
    path('api/v1/', v1_api.urls),
    path('api/core/', core_api.urls),
    # ── Comptes & navigation ──────────────────────────────────
    path('accounts/', include('accounts.urls')),
    path('gestion/', include('accounts.gestion_urls')),
    path('core/', include('core.urls')),
    # ── Compositions & corrections ────────────────────────────
    path('exams/', include('exams.urls')),
    path('examens-nationaux/', include('exams.examens_nationaux_urls')),
    path('compositions/', include('compositions.urls')),
    path('corrections/', include('corrections.urls')),
    path('qcm/', include('qcm.urls')),
    # ── Cours & devoirs ───────────────────────────────────────
    path('cours/', include('cours.urls')),
    path('devoirs/', include('devoirs.urls')),
    # ── Paiements ─────────────────────────────────────────────
    path('payments/', include('payments.urls')),
    path('subscriptions/', include('subscriptions.urls')),
    # ── Infrastructure ────────────────────────────────────────
    path('notifications/', include('notifications.urls')),
    path('audit/', include('audittrail.urls')),
    path('webhooks/', include('webhooks.urls')),
]

# Servir les fichiers médias et statiques en développement (RIGOUREUX)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += staticfiles_urlpatterns()

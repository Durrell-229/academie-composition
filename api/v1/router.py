from ninja import NinjaAPI
from ninja.security import django_auth
from .auth import router as auth_router
from .examens import router as examens_router
from .compositions import router as compositions_router
from .correction import router as correction_router
from .tutor import router as tutor_router
from .notifications import router as notifications_router
from .bulletins import router as bulletins_router

# auth=django_auth par défaut sur tous les endpoints sauf /auth
api = NinjaAPI(title="Académie Numérique API", version="1.0.0", auth=django_auth)

api.add_router("/auth", auth_router, tags=["Authentification"], auth=None)
api.add_router("/examens", examens_router, tags=["Examens"])
api.add_router("/compositions", compositions_router, tags=["Compositions"])
api.add_router("/correction", correction_router, tags=["Correction"])
api.add_router("/tutor", tutor_router, tags=["Tuteur IA"])
api.add_router("/notifications", notifications_router, tags=["Notifications Globales"])
api.add_router("/bulletins", bulletins_router, tags=["Bulletins"])

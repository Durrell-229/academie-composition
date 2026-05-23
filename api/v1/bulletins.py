"""
API endpoints pour la gestion des bulletins scolaires
"""

import uuid
from ninja import Router
from ninja.errors import HttpError
from django.shortcuts import get_object_or_404

router = Router()


@router.post("/generate/{eleve_id}")
def generate_bulletin(request, eleve_id: uuid.UUID):
    """Récupère le dernier bulletin disponible pour un élève donné."""
    from devoirs.models import BulletinDevoir
    from django.contrib.auth import get_user_model

    User = get_user_model()
    # Vérifier que l'élève existe
    get_object_or_404(User, id=eleve_id)

    bulletin = BulletinDevoir.objects.filter(eleve_id=eleve_id).last()
    if not bulletin:
        raise HttpError(404, "Aucun bulletin trouvé pour cet élève")

    return {"id": str(bulletin.id), "status": "ok"}

import logging
import uuid
from typing import List, Optional
from ninja import Router, Schema
from django.shortcuts import get_object_or_404
from bulletins.models import Bulletin, BulletinLigne

logger = logging.getLogger(__name__)
router = Router()


class BulletinLigneOut(Schema):
    matiere: str
    note: float
    note_max: float
    coefficient: float
    appreciation: str


class BulletinOut(Schema):
    id: uuid.UUID
    periode: str
    type_bulletin: str
    moyenne_generale: float
    rang: int
    effectif_classe: int


@router.get("/{eleve_id}", response=List[BulletinOut])
def list_eleve_bulletins(request, eleve_id: uuid.UUID):
    user = request.user
    # Élève ne peut accéder qu'à ses propres bulletins
    if user.role == 'eleve' and str(user.id) != str(eleve_id):
        return []
    # Parent ne peut accéder qu'aux bulletins de ses enfants
    if user.role == 'parent':
        enfants_ids = list(user.enfants.values_list('eleve_id', flat=True))
        if eleve_id not in enfants_ids:
            return []
    return Bulletin.objects.filter(eleve_id=eleve_id).order_by('-created_at')


@router.post("/generate/{eleve_id}")
def generate_bulletin(request, eleve_id: uuid.UUID, periode: str):
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # Seuls admin et conseiller peuvent générer un bulletin
    if request.user.role not in ('admin', 'conseiller'):
        return {"error": "Permission refusée"}, 403

    eleve = get_object_or_404(User, id=eleve_id)

    # Vérifier qu'un bulletin n'existe pas déjà pour cette période
    existing = Bulletin.objects.filter(eleve=eleve, periode=periode).first()
    if existing:
        return {"message": "Bulletin déjà existant", "bulletin_id": str(existing.id)}

    try:
        bulletin = Bulletin.objects.create(
            eleve=eleve,
            periode=periode,
            classe=getattr(eleve, 'classe', ''),
            annee_scolaire=getattr(eleve, 'annee_scolaire', ''),
        )
        return {"success": True, "bulletin_id": str(bulletin.id)}
    except Exception as e:
        logger.error(f"generate_bulletin eleve={eleve_id} periode={periode}: {e}", exc_info=True)
        return {"error": "Erreur lors de la génération du bulletin"}, 500

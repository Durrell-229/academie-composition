from ninja import Router, Schema
from ninja.pagination import paginate, PageNumberPagination
from compositions.models import Resultat
import uuid
from typing import List

router = Router()

class ResultatOut(Schema):
    id: uuid.UUID
    eleve_name: str
    exam_titre: str
    note: float
    mention: str

    @staticmethod
    def resolve_eleve_name(obj):
        return obj.session.eleve.full_name

    @staticmethod
    def resolve_exam_titre(obj):
        return obj.session.exam.titre

@router.get("/", response=List[ResultatOut])
@paginate(PageNumberPagination, page_size=25)
def list_results(request):
    return Resultat.objects.select_related('session__eleve', 'session__exam').all()

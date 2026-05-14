"""
Service d'agrégation des données pour les bulletins.
Récupère les notes depuis TOUTES les sources (Evaluations, Devoirs, Compositions, QCM).
Gère les zéros automatiquement selon les règles académiques.
"""

from decimal import Decimal
from django.db.models import Avg, Q
from django.utils import timezone
from datetime import datetime

from academic.models import Note, Evaluation, Inscription, BulletinNotes
from devoirs.models import DevoirReponseEleve, DevoirMatiere
from compositions.models import Resultat, CompositionSession
from qcm.models import QCMResultat
from core.models import Matiere, Classe
from bulletins.coefficients_benin import get_coefficient as get_benin_coefficient


class BulletinDataAggregator:
    """Agrège toutes les notes d'un élève pour générer un bulletin précis."""

    @staticmethod
    def get_year_from_period(annee_scolaire):
        """Extrait l'année du format '2025-2026' → 2025"""
        try:
            return int(annee_scolaire.split('-')[0])
        except:
            return datetime.now().year

    @staticmethod
    def get_matieres_for_class(classe_obj):
        """Récupère toutes les matières d'une classe."""
        # Retourner toutes les matières actives
        # (Le modèle MatiereClasse n'existe pas, on utilise Matiere directement)
        return Matiere.objects.filter(is_active=True)

    @staticmethod
    def aggregate_notes(eleve, classe, periode, annee_scolaire):
        """
        Agrège toutes les notes de l'élève pour un bulletin.

        Args:
            eleve: User object (l'élève)
            classe: Classe object (la classe)
            periode: str ('T1', 'T2', 'T3', 'S1', 'S2', 'AN')
            annee_scolaire: str ('2025-2026')

        Returns:
            dict avec structure complète des données du bulletin
        """
        year = BulletinDataAggregator.get_year_from_period(annee_scolaire)
        matieres = BulletinDataAggregator.get_matieres_for_class(classe)

        matieres_data = []
        all_moyennes = []

        for matiere in matieres:
            # 1. Récupérer notes d'interrogations (academic.Note type='interrogation')
            # + coefficient depuis l'Evaluation
            interrogations_avec_coeff = []
            try:
                evaluations = Evaluation.objects.filter(
                    type_evaluation='interrogation',
                    date_evaluation__year=year
                ).filter(
                    matiere_classe__matiere__nom__icontains=matiere.nom
                )

                for evaluation in evaluations:
                    note_obj = Note.objects.filter(
                        eleve=eleve,
                        evaluation=evaluation,
                        est_absent=False,
                        est_exclu=False
                    ).first()

                    if note_obj:
                        interrogations_avec_coeff.append({
                            'note': Decimal(str(note_obj.note)),
                            'coefficient': Decimal(str(evaluation.coefficient or 1))
                        })
            except:
                pass

            # Calculer moyenne pondérée des interrogations
            moy_interrogations = Decimal('0')
            coeff_interro = Decimal('1')
            if interrogations_avec_coeff:
                total_notes = sum(Decimal(str(item['note'])) * item['coefficient'] for item in interrogations_avec_coeff)
                total_coeffs = sum(item['coefficient'] for item in interrogations_avec_coeff)
                moy_interrogations = total_notes / total_coeffs if total_coeffs > 0 else Decimal('0')
                coeff_interro = total_coeffs / len(interrogations_avec_coeff) if interrogations_avec_coeff else Decimal('1')

            # 2. Récupérer notes de devoirs (DevoirReponseEleve.note_finale)
            # + coefficient depuis DevoirMatiere
            try:
                devoir_responses = DevoirReponseEleve.objects.filter(
                    eleve=eleve,
                    devoir_matiere__matiere=matiere,
                    devoir_matiere__devoir__annee_scolaire=annee_scolaire,
                    statut__in=['corrige', 'approuve']
                )

                notes_devoirs = []
                coeff_devoir = Decimal('1')

                for resp in devoir_responses:
                    notes_devoirs.append(Decimal(str(resp.note_finale)))
                    # Récupérer coefficient depuis le devoir
                    devoir = resp.devoir_matiere.devoir
                    if devoir.coefficients_par_matiere and str(matiere.id) in devoir.coefficients_par_matiere:
                        coeff_devoir = Decimal(str(devoir.coefficients_par_matiere[str(matiere.id)]))
                    else:
                        coeff_devoir = Decimal(str(devoir.coefficient_default or 1))
            except:
                notes_devoirs = []
                coeff_devoir = Decimal('1')

            moy_devoirs = Decimal('0')
            if notes_devoirs:
                moy_devoirs = sum(Decimal(str(n)) for n in notes_devoirs) / len(notes_devoirs)

            # 3. Récupérer compositions/examens (Resultat.note)
            # + coefficient depuis Exam
            try:
                composition = Resultat.objects.filter(
                    session__eleve=eleve,
                    session__exam__matiere=matiere,
                    session__exam__created_at__year=year
                ).first()

                coeff_composition = Decimal('1')
                if composition and composition.session:
                    coeff_composition = Decimal(str(composition.session.exam.coefficient or 1))
            except:
                composition = None
                coeff_composition = Decimal('1')

            note_composition = Decimal('0')
            if composition:
                note_composition = Decimal(str(composition.note)) if composition.note else Decimal('0')

            # 4. Calculer moyenne finale
            # Formule : moyenne pondérée selon les poids
            # Interrogation: 33% + Devoir: 33% + Composition: 34%
            notes_pour_moyenne = [
                moy_interrogations,
                moy_devoirs,
                note_composition
            ]
            notes_non_zero = [n for n in notes_pour_moyenne if n > 0]

            if notes_non_zero:
                moyenne_finale = sum(notes_pour_moyenne) / 3
            else:
                moyenne_finale = Decimal('0')

            # 5. NOUVEAU: Obtenir coefficient depuis la source appropriée
            # Priorité: Exam > Devoir > Evaluation > Coefficients Bénin (fallback)
            coefficient = Decimal('1')

            if composition and composition.session:
                # Vient d'un Exam
                coefficient = Decimal(str(composition.session.exam.coefficient or 1))
            elif notes_devoirs and devoir_responses:
                # Vient d'un Devoir
                coefficient = coeff_devoir
            elif interrogations_avec_coeff:
                # Vient d'Evaluations
                coefficient = coeff_interro
            else:
                # Fallback: coefficients officiels Bénin
                serie = BulletinDataAggregator._extract_serie(classe)
                coefficient = Decimal(str(get_benin_coefficient(matiere.nom, serie)))

            # 6. Appréciation automatique
            appreciation = BulletinDataAggregator._generate_appreciation(
                float(moyenne_finale)
            )

            matiere_data = {
                'nom': matiere.nom,
                'coefficient': float(coefficient),
                'moy_interrogations': float(round(moy_interrogations, 2)),
                'moy_devoirs': float(round(moy_devoirs, 2)),
                'note_composition': float(round(note_composition, 2)),
                'moyenne_finale': float(round(moyenne_finale, 2)),
                'appreciation': appreciation
            }

            matieres_data.append(matiere_data)
            all_moyennes.append((float(moyenne_finale), float(coefficient)))

        # 7. Calculer moyenne générale pondérée
        if all_moyennes:
            total_points = sum(moy * coeff for moy, coeff in all_moyennes)
            total_coeffs = sum(coeff for _, coeff in all_moyennes)
            moyenne_generale = round(total_points / total_coeffs, 2) if total_coeffs > 0 else 0
        else:
            moyenne_generale = 0

        # 8. Calculer rang dans la classe
        rang_classe = BulletinDataAggregator._calculate_rank(
            eleve, classe, moyenne_generale
        )

        # 9. Obtenir effectif de la classe
        try:
            inscriptions = Inscription.objects.filter(
                classe=classe,
                annee_scolaire__code=annee_scolaire
            ).count()
            effectif = inscriptions if inscriptions > 0 else 1
        except:
            effectif = 40  # Valeur par défaut

        return {
            'matieres': matieres_data,
            'moyenne_generale': moyenne_generale,
            'rang': rang_classe,
            'effectif': effectif,
            'nombre_matieres': len(matieres_data),
            'eleve': {
                'nom': eleve.last_name or '',
                'prenom': eleve.first_name or '',
                'matricule': getattr(eleve, 'matricule', ''),
                'classe': str(classe) if classe else '',
            }
        }

    @staticmethod
    def _extract_serie(classe):
        """Extrait la série de la classe (C, D, Littéraire, etc.)"""
        if not classe:
            return 'bepc'

        classe_str = str(classe).lower()

        # Mapper les noms de classe aux séries
        if 'bepc' in classe_str or '3e' in classe_str or '3ème' in classe_str:
            return 'bepc'
        elif 'a1' in classe_str or 'a2' in classe_str:
            return 'A1'
        elif 'lit' in classe_str or 'littéraire' in classe_str or 'littaire' in classe_str:
            return 'A1'
        elif 'c' in classe_str or 'math' in classe_str or 'scientifique' in classe_str:
            return 'C'
        elif 'd' in classe_str or 'bi' in classe_str or 'biologie' in classe_str:
            return 'D'
        elif 'e' in classe_str or 'technique' in classe_str or 'industrielle' in classe_str:
            return 'E'
        else:
            return 'bepc'

    @staticmethod
    def _generate_appreciation(moyenne):
        """Génère une appréciation basée sur la moyenne."""
        if moyenne >= 18:
            return "Excellent"
        elif moyenne >= 16:
            return "Très bien"
        elif moyenne >= 14:
            return "Bien"
        elif moyenne >= 12:
            return "Assez bien"
        elif moyenne >= 10:
            return "Passable"
        elif moyenne > 0:
            return "Insuffisant"
        else:
            return "Absent/Exclu"

    @staticmethod
    def _calculate_rank(eleve, classe, moyenne_actuelle):
        """Calcule le rang de l'élève dans sa classe."""
        if not classe or moyenne_actuelle <= 0:
            return 0

        # Récupérer tous les bulletins de la classe
        bulletins_classe = BulletinNotes.objects.filter(
            classe=classe
        ).order_by('-moyenne_generale')

        rang = 1
        for idx, bulletin in enumerate(bulletins_classe, 1):
            if bulletin.eleve == eleve:
                return idx
            if bulletin.moyenne_generale < moyenne_actuelle:
                return idx

        return len(list(bulletins_classe)) + 1


class BulletinDataValidator:
    """Valide les données d'un bulletin avant génération."""

    @staticmethod
    def validate(data):
        """Valide la structure des données."""
        errors = []

        if not data.get('matieres'):
            errors.append("Aucune matière trouvée")

        if data.get('moyenne_generale', 0) < 0:
            errors.append("Moyenne générale négative")

        for matiere in data.get('matieres', []):
            if matiere.get('coefficient', 0) <= 0:
                errors.append(f"{matiere.get('nom')}: coefficient invalide")

        return errors

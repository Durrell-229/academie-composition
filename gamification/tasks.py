import logging
from datetime import date
from django.db.models import Avg, Count, Q

from accounts.models import User
from compositions.models import Resultat
from .models import Badge, UserBadge, GlobalLeaderboard, XPAction, StreakRecord

logger = logging.getLogger(__name__)

# Points XP par action
XP_REWARDS = {
    'composition_soumise': 15,
    'note_excellente': 50,
    'note_tres_bien': 30,
    'note_bien': 20,
    'premiere_composition': 25,
    'serie_3_jours': 20,
    'serie_7_jours': 50,
    'serie_30_jours': 200,
    'badge_obtenu': 10,
    'certificat_obtenu': 30,
    'qcm_parfait': 40,
    'zero_triche': 15,
}


def award_xp(user, action: str, description: str = ''):
    points = XP_REWARDS.get(action, 0)
    if points > 0:
        XPAction.objects.create(user=user, action=action, points_gagnes=points, description=description)
        # Update streak
        streak, _ = StreakRecord.objects.get_or_create(user=user)
        streak.update_streak()


def check_and_award_badges(user):
    """Vérifie et attribue les badges à un utilisateur."""
    badges_to_check = Badge.objects.filter(est_actif=True)
    earned_badge_ids = set(UserBadge.objects.filter(user=user).values_list('badge_id', flat=True))

    resultats = Resultat.objects.filter(session__eleve=user)
    nb_compositions = resultats.count()
    nb_excellentes = resultats.filter(mention='excellent').count()
    avg_note = resultats.aggregate(avg=Avg('note'))['avg'] or 0

    for badge in badges_to_check:
        if badge.id in earned_badge_ids:
            continue

        earned = False
        cond = badge.condition_obtention

        if cond.get('type') == 'compositions' and nb_compositions >= cond.get('valeur', 999):
            earned = True
        elif cond.get('type') == 'excellentes' and nb_excellentes >= cond.get('valeur', 999):
            earned = True
        elif cond.get('type') == 'moyenne' and avg_note >= cond.get('valeur', 999):
            earned = True
        elif cond.get('type') == 'streak':
            streak = StreakRecord.objects.filter(user=user).first()
            if streak and streak.current_streak >= cond.get('valeur', 999):
                earned = True

        if earned:
            UserBadge.objects.create(user=user, badge=badge)
            award_xp(user, 'badge_obtenu', f'Badge: {badge.nom}')


def update_global_leaderboard():
    """Met à jour le classement mondial."""
    today = date.today()

    users = User.objects.filter(role='eleve', is_active=True)
    for user in users:
        resultats = Resultat.objects.filter(session__eleve=user)
        if not resultats.exists():
            continue

        stats = resultats.aggregate(
            total=Count('id'),
            avg=Avg('note'),
            excellentes=Count('id', filter=Q(mention='excellent')),
        )

        xp_total = sum(a.points_gagnes for a in XPAction.objects.filter(user=user))
        level = max(1, xp_total // 100 + 1)
        streak = StreakRecord.objects.filter(user=user).first()

        GlobalLeaderboard.objects.update_or_create(
            user=user, periode='all_time', date_periode=date(2000, 1, 1),
            defaults={
                'score_total': float(stats['avg'] or 0) * stats['total'],
                'nb_compositions': stats['total'],
                'nb_excellentes': stats['excellentes'],
                'moyenne': stats['avg'] or 0,
                'points_xp': xp_total,
                'niveau': level,
                'streak_jours': streak.current_streak if streak else 0,
                'pays': user.country,
            }
        )

    # Recalculer les rangs
    entries = GlobalLeaderboard.objects.filter(periode='all_time').order_by('-score_total')
    for idx, entry in enumerate(entries, 1):
        entry.rang_mondial = idx
        entry.save(update_fields=['rang_mondial'])

    # Rangs nationaux
    countries = entries.values_list('pays', flat=True).distinct()
    for country in countries:
        national = entries.filter(pays=country).order_by('-score_total')
        for idx, entry in enumerate(national, 1):
            entry.rang_national = idx
            entry.save(update_fields=['rang_national'])

    logger.info(f"Classement mondial mis à jour: {entries.count()} entrées")


def create_default_badges():
    """Crée les badges par défaut du système."""
    default_badges = [
        {'nom': 'Premier Pas', 'description': 'Avoir soumis sa première composition', 'icone': '🎯', 'categorie': 'participation', 'points': 10, 'rarete': 'commun', 'condition_obtention': {'type': 'compositions', 'valeur': 1}},
        {'nom': 'Régulier', 'description': 'Avoir soumis 5 compositions', 'icone': '📝', 'categorie': 'participation', 'points': 25, 'rarete': 'commun', 'condition_obtention': {'type': 'compositions', 'valeur': 5}},
        {'nom': 'Assidu', 'description': 'Avoir soumis 20 compositions', 'icone': '📚', 'categorie': 'participation', 'points': 50, 'rarete': 'rare', 'condition_obtention': {'type': 'compositions', 'valeur': 20}},
        {'nom': 'Première Excellence', 'description': 'Obtenir une note excellente (>=95%)', 'icone': '⭐', 'categorie': 'excellence', 'points': 30, 'rarete': 'rare', 'condition_obtention': {'type': 'excellentes', 'valeur': 1}},
        {'nom': 'Cumul d\'Excellence', 'description': 'Obtenir 5 notes excellentes', 'icone': '🌟', 'categorie': 'excellence', 'points': 100, 'rarete': 'epique', 'condition_obtention': {'type': 'excellentes', 'valeur': 5}},
        {'nom': 'Moyenne d\'Or', 'description': 'Maintenir une moyenne >= 16/20', 'icone': '🥇', 'categorie': 'academique', 'points': 75, 'rarete': 'epique', 'condition_obtention': {'type': 'moyenne', 'valeur': 16}},
        {'nom': 'Série de 3', 'description': '3 jours consécutifs d\'activité', 'icone': '🔥', 'categorie': 'progression', 'points': 20, 'rarete': 'commun', 'condition_obtention': {'type': 'streak', 'valeur': 3}},
        {'nom': 'Série de 7', 'description': '7 jours consécutifs d\'activité', 'icone': '💪', 'categorie': 'progression', 'points': 50, 'rarete': 'rare', 'condition_obtention': {'type': 'streak', 'valeur': 7}},
        {'nom': 'Série de 30', 'description': '30 jours consécutifs d\'activité', 'icone': '🏅', 'categorie': 'progression', 'points': 200, 'rarete': 'legendaire', 'condition_obtention': {'type': 'streak', 'valeur': 30}},
        {'nom': 'Intègre', 'description': 'Jamais de tentative de triche', 'icone': '🛡️', 'categorie': 'special', 'points': 15, 'rarete': 'commun', 'condition_obtention': {'type': 'zero_triche', 'valeur': 1}},
    ]

    created = 0
    for data in default_badges:
        _, c = Badge.objects.get_or_create(nom=data['nom'], defaults=data)
        created += 1 if c else 0

    logger.info(f"{created} badges par défaut créés")

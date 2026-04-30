from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import date

from .models import Badge, UserBadge, GlobalLeaderboard, XPAction, StreakRecord


@login_required
def leaderboard_view(request):
    periode = request.GET.get('periode', 'all_time')
    entries = GlobalLeaderboard.objects.filter(
        periode=periode,
        date_periode=date.today() if periode != 'all_time' else date(2000, 1, 1),
    ).select_related('user')[:100]

    # Si pas d'entrées, afficher tous les temps
    if not entries.exists():
        entries = GlobalLeaderboard.objects.filter(periode='all_time').select_related('user')[:100]

    user_rank = None
    try:
        user_rank = GlobalLeaderboard.objects.filter(
            periode=periode, user=request.user
        ).first()
    except Exception:
        pass

    return render(request, 'gamification/leaderboard.html', {
        'entries': entries,
        'user_rank': user_rank,
        'periode': periode,
    })


@login_required
def my_badges_view(request):
    badges = UserBadge.objects.filter(user=request.user).select_related('badge')
    all_badges = Badge.objects.filter(est_actif=True)
    earned_ids = set(badges.values_list('badge_id', flat=True))
    return render(request, 'gamification/my_badges.html', {
        'badges': badges,
        'all_badges': all_badges,
        'earned_ids': earned_ids,
    })


@login_required
def my_progress_view(request):
    streak, _ = StreakRecord.objects.get_or_create(user=request.user)
    xp_total = sum(a.points_gagnes for a in XPAction.objects.filter(user=request.user))
    level = max(1, xp_total // 100 + 1)
    xp_next_level = (level) * 100
    xp_progress = xp_total % 100

    leaderboard_entry = GlobalLeaderboard.objects.filter(
        user=request.user, periode='all_time'
    ).first()

    return render(request, 'gamification/progress.html', {
        'streak': streak,
        'xp_total': xp_total,
        'level': level,
        'xp_next_level': xp_next_level,
        'xp_progress': xp_progress,
        'leaderboard_entry': leaderboard_entry,
    })


@login_required
def leaderboard_api(request):
    periode = request.GET.get('periode', 'all_time')
    entries = GlobalLeaderboard.objects.filter(periode=periode).select_related('user')[:50]
    data = [{
        'rang': e.rang_mondial,
        'nom': e.user.full_name,
        'pays': e.pays,
        'score': float(e.score_total),
        'niveau': e.niveau,
        'moyenne': float(e.moyenne),
        'compositions': e.nb_compositions,
    } for e in entries]
    return JsonResponse({'leaderboard': data})

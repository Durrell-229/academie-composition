"""
Real-time notifications using Server-Sent Events (SSE).
Allows pushing notifications to clients without polling.
"""
import json
import time
import logging
from django.http import StreamingHttpResponse
from django.contrib.auth.decorators import login_required
from .models import Notification

logger = logging.getLogger(__name__)


@login_required
def notification_stream(request):
    """
    SSE endpoint - keeps connection open and pushes notifications to client.
    Client receives event when new notification is created.
    """
    def event_stream():
        user_id = request.user.id
        last_notification_count = Notification.objects.filter(
            recipient_id=user_id
        ).count()

        while True:
            try:
                # Check for new notifications every 2 seconds
                time.sleep(2)
                
                current_count = Notification.objects.filter(
                    recipient_id=user_id
                ).count()
                
                if current_count > last_notification_count:
                    # New notification detected
                    unread_count = Notification.objects.filter(
                        recipient_id=user_id,
                        is_read=False
                    ).count()
                    
                    # Get the latest notification
                    latest = Notification.objects.filter(
                        recipient_id=user_id
                    ).order_by('-created_at').first()
                    
                    data = {
                        'type': 'new_notification',
                        'unread_count': unread_count,
                        'notification': {
                            'id': latest.id if latest else None,
                            'title': latest.title if latest else '',
                            'message': latest.message if latest else '',
                            'type': latest.type if latest else '',
                            'created_at': latest.created_at.isoformat() if latest else None,
                        }
                    }
                    
                    yield f"data: {json.dumps(data)}\n\n"
                    last_notification_count = current_count
                
                # Send heartbeat to keep connection alive
                yield f": heartbeat\n\n"
                
            except GeneratorExit:
                logger.info(f"SSE connection closed for user {user_id}")
                break
            except Exception as e:
                logger.error(f"SSE error for user {user_id}: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': 'Connection error'})}\n\n"
                break

    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream',
    )
    # Prevent buffering in nginx/proxies
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@login_required
def unread_count_view(request):
    """Get current unread notification count (JSON API)."""
    count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    from django.http import JsonResponse
    return JsonResponse({'unread_count': count})

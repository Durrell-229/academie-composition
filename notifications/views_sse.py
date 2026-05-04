"""
Real-time notifications using Server-Sent Events (SSE).
Allows pushing notifications to clients without polling.
"""
import json
import time
import logging
from django.http import StreamingHttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Notification

logger = logging.getLogger(__name__)


@login_required
def notification_stream(request):
    """
    SSE endpoint - DISABLED on Render due to Gunicorn sync worker issues.
    Falls back to simple polling via unread_count_view API.
    """
    # Return empty SSE stream to avoid blocking Gunicorn workers
    def event_stream():
        try:
            # Send initial connection event
            data = {
                'type': 'connected',
                'message': 'SSE disabled in production - use polling API instead'
            }
            yield f"data: {json.dumps(data)}\n\n"
            
            # Close connection immediately to prevent worker timeout
            yield f": connection closed\n\n"
            
        except GeneratorExit:
            logger.info(f"SSE connection closed for user {request.user.id}")
            return  # GeneratorExit - just stop
        except Exception as e:
            logger.error(f"SSE error for user {request.user.id}: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

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

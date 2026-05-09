from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/exam/(?P<exam_id>\\d+)/$', consumers.ExamRoomConsumer.as_asgi()),
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r'ws/bulletin/$', consumers.BulletinUpdateConsumer.as_asgi()),
]

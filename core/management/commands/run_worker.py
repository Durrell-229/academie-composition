import signal
import logging
from django.core.management.base import BaseCommand
from core.redis_tasks import process_task_queue

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run Redis background task worker (no Celery needed)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-tasks', type=int, default=None,
            help='Stop after processing N tasks (useful for testing)'
        )

    def handle(self, *args, **options):
        max_tasks = options['max_tasks']
        shutdown_event = signal_event()

        self.stdout.write(self.style.SUCCESS(
            f"Starting Redis worker (max_tasks={max_tasks or 'unlimited'})..."
        ))
        self.stdout.write("Press Ctrl+C to stop.\n")

        try:
            process_task_queue(max_tasks=max_tasks, shutdown_event=shutdown_event)
        except KeyboardInterrupt:
            self.stdout.write("\nWorker stopped.")


def signal_event():
    """Create a threading Event that gets set on SIGTERM/SIGINT."""
    import threading
    event = threading.Event()

    def handler(signum, frame):
        event.set()

    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)
    return event

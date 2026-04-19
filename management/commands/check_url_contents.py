from django.core.management.base import BaseCommand

from ...models import UrlContentTracker

class Command(BaseCommand):
    def handle(self, *args, **options):
        for tracker in UrlContentTracker.objects.all():
            if tracker.needs_check():
                tracker.do_check()

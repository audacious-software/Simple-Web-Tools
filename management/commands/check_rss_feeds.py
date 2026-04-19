from django.core.management.base import BaseCommand

from ...models import RssFeed

class Command(BaseCommand):
    def handle(self, *args, **options):
        for feed in RssFeed.objects.all():
            if feed.needs_check():
                feed.do_check()

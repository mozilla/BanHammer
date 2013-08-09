from django.core.management.base import BaseCommand, CommandError
from BanHammer.blacklist import models
from BanHammer.blacklist.views import blacklist

import datetime

class Command(BaseCommand):
    help = 'Clean old blacklists'
    
    def handle(self, *args, **options):
        self._remove_outdated_blacklists()

    def _remove_outdated_blacklists(self):
        blacklists = models.Blacklist.objects.filter(end_date__lt=datetime.datetime.now(),
                                        suggestion=False, removed=False)
        for b in blacklists:
            blacklist._delete_pre(b, b.offender, b.type)
            b.removed = True
            b.save()

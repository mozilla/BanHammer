from django.core.management.base import BaseCommand, CommandError
from BanHammer.blacklist import models
from BanHammer.blacklist import tasks

class Command(BaseCommand):
    help = 'Update ZLBs data'
    
    def handle(self, *args, **options):
        self._update_zlbs()

    def _update_zlbs(self):
        zlbs = models.ZLB.objects.all()
        for zlb in zlbs:
            tasks.update_zlb.delay(zlb.id)

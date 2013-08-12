from django.core.management.base import BaseCommand, CommandError
from BanHammer.blacklist import models

class Command(BaseCommand):
    help = 'Decrease attack scores'
    
    def handle(self, *args, **options):
        self._decrease_attack_scores()

    def _decrease_attack_scores(self):
        config_o = models.Config.objects.get(key="score_decrease")
        decrease_factor = int(config_o.value)
        offenders_o = models.Offender.objects.all()
        for offender in offenders_o:
            if offender.score - decrease_factor >= 0:
                offender.score -= decrease_factor
                offender.save()

from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from BanHammer.blacklist.models import  Config, Event, Offender, Blacklist,\
                                        AttackScoreHistory, WhitelistIP
from BanHammer.blacklist.management import notifications
from BanHammer.blacklist import tasks

DEBUG = True

class Command(BaseCommand):
    help = 'Create a new event'
    option_list = BaseCommand.option_list
    option_list += (
        make_option('--attackerAddress',
            action='store',
            dest='attackerAddress',
            help="IP address of the attacker",
        ),
        make_option('--rulename',
            action="store",
            dest="rulename",
            help="Name of the ArcSight rule that matched",
        ),
        make_option('--severity',
            action="store",
            dest="severity",
            type=int,
            help="Severity of the alert",
        ),
        make_option('--eventId',
            action="store",
            dest="eventId",
            type=int,
            help="Event ID",
        ),
        make_option('--attackerUserName',
            action="store",
            dest="attackerUserName",
            help="(opt) Username tried by the attacker",
        ),
        make_option('--requestUrl',
            action="store",
            dest="requestUrl",
            help="(opt) Request URL",
        ),
        make_option('--requestUrlHost',
            action="store",
            dest="requestUrlHost",
            help="(opt) Host Serving the requested URL?",
        ),
        make_option('--sourceGeoCountryName',
            action="store",
            dest="sourceGeoCountryName",
            help="(opt) Country of the source IP address",
        ),
        make_option('--requestContext',
            action="store",
            dest="requestContext",
            help="(opt) ?",
        ),
        make_option('--targetHostName',
            action="store",
            dest="targetHostName",
            help="(opt) Targeted hostname?",
        ),
        make_option('--targetAddress',
            action="store",
            dest="targetAddress",
            help="(opt) ?",
        ),
        make_option('--sourceAddress',
            action="store",
            dest="sourceAddress",
            help="(opt) Source IP address",
        ),
        make_option('--login',
            action="store",
            dest="login",
            help="(opt) ?",
        ),
        make_option('--referrer',
            action="store",
            dest="referrer",
            help="(opt) ?",
        ),
        make_option('--sourceUserName',
            action="store",
            dest="sourceUserName",
            help="(opt) ?",
        ),
        make_option('--fileName',
            action="store",
            dest="fileName",
            help="(opt) ?",
        ),
        make_option('--getDestHostName',
            action="store",
            dest="getDestHostName",
            help="(opt) ?",
        ),
    )

    def handle(self, *args, **options):
        if options['attackerAddress'] == None:
            raise Exception('--attackerAddress argument required')
        if options['rulename'] == None:
            raise Exception('--rulename argument required')
        if options['severity'] == None:
            raise Exception('--severity argument required')
        if options['eventId'] == None:
            raise Exception('--eventId argument required')
        if DEBUG:
            self.stdout.write('args %s' % str(args))
            self.stdout.write('\n')
            self.stdout.write('options %s' % str(options))
            self.stdout.write('\n')
        
        for i in ['settings', 'pythonpath', 'traceback', 'verbosity']:
            del options[i]
            
        event = self._save_event(options)
        if not WhitelistIP.is_ip_in(event.attackerAddress):
            offender = Offender.find_create_from_ip(event.attackerAddress)
            score_indicators = AttackScoreHistory.score_indicators(event, offender)
            score_factors = self._get_score_factors()
            score_details = Offender.compute_attackscore(score_indicators, score_factors)
            attackscore_history_kwargs = self._get_attackscore_history_kwargs(offender,
                event, score_details, score_indicators)
            self._save_attackscore_history(attackscore_history_kwargs)
            offenderscore = Offender.compute_offenderscore(offender, score_details['total'])
            self._save_offenderscore(offender, offenderscore)
            tasks.notification_new_event.delay(
                offender.__dict__,
                event.__dict__,
                score_factors,
                attackscore_history_kwargs)

    def _save_event(self, options):
        event = Event(**options)
        event.save()
        return event
    
    def _save_offenderscore(self, offender, score):
        offender.score = score
        offender.save()
    
    def _get_score_factors(self):
        score_factors = {}
        for i in Config.objects.filter(key__regex=r'^score_factor_'):
            score_factors[i.key[13:]] = int(i.value)
        return score_factors
    
    def _get_attackscore_history_kwargs(self, offender, event, score_details, score_indicators):
        kwargs = score_indicators
        kwargs['offender'] = offender
        kwargs['event'] = event
        for i in score_details:
            kwargs[i+'_score'] = score_details[i]
        return kwargs
            
    def _save_attackscore_history(self, kwargs):
        AttackScoreHistory(**kwargs).save()

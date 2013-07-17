from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import datetime
from BanHammer.blacklist.models import Event, Offender, AttackScore, Blacklist

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
        score = self._save_score(event)
        # TODO: _create_blacklist (if score > threshold, TODO: auto)
        # TODO: send notifications
            
    def _save_event(self, options):
        event = Event(**options)
        event.save()
        return event
        
    def _save_score(self, event):
        offender = Offender.find_create_from_ip(event.attackerAddress)
        
        # previous events number
        one_day = datetime.datetime.today() - datetime.timedelta(1)
        event_types = Event.objects.filter(created_date__gte=one_day,
            attackerAddress=event.attackerAddress)
        event_types = uniquify(event_types.values('rulename'))
        event_types = len(event_types)-1
        
        # number of times bgp blocked
        times_bgp_blocked = Blacklist.objects.filter(
            offender=offender,
            type='bgp_block'
        ).count()
        
        # number of times zlb blocked
        times_zlb_blocked = Blacklist.objects.filter(
            offender=offender,
            type='zlb_block'
        ).count()
        
        # number of times redirected
        times_zlb_redirected = Blacklist.objects.filter(
            offender=offender.id,
            type='zlb_redirect'
        ).count()
        
        # last attack score of the offender
        last_attack_score = AttackScore.objects.filter(
            offender=offender)
        if len(last_attack_score) > 0:
            last_attack_score = last_attack_score[0]
        else:
            last_attack_score = 0
        
        if DEBUG:
            self.stdout.write('severity %i\n' % event.severity)
            self.stdout.write('different event types %i\n' % event_types)
            self.stdout.write('times bgp blocked %i\n' % times_bgp_blocked)
            self.stdout.write('times zlb blocked %i\n' % times_zlb_blocked)
            self.stdout.write('times zlb redirected %i\n' % times_zlb_redirected)
            self.stdout.write('last attack score %i\n' % last_attack_score)
        
        # TODO: compute attack score
        #AttackScore.compute()
        #    AttackScore.find_or_create_from_offender()
                
        # TODO: add attack score
        
def uniquify(items):
    checked = []
    for i in items:
        if i['rulename'] not in checked:
            checked.append(i['rulename'])
    return checked

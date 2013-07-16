from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from BanHammer.blacklist.models import Event

DEBUG = True

class Command(BaseCommand):
    help = 'Create a new event'
    option_list = BaseCommand.option_list
    option_list += (
        make_option('--ip',
            action='store',
            dest='ip',
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
        make_option('--eventID',
            action="store",
            dest="eventID",
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
        if options['ip'] == None:
            raise Exception('--ip argument required')
        if options['rulename'] == None:
            raise Exception('--rulename argument required')
        if options['severity'] == None:
            raise Exception('--severity argument required')
        if options['eventID'] == None:
            raise Exception('--eventID argument required')
        if DEBUG:
            self.stdout.write('args %s' % str(args))
            self.stdout.write('\n')
            self.stdout.write('options %s' % str(options))
            self.stdout.write('\n')

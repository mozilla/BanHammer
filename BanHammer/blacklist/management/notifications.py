from django.core.mail import send_mail

from BanHammer.blacklist.models import Config
from BanHammer import settings

def email_enabled():
    return bool(Config.objects.get(key="notifications_email_enable").value)

def send_email_new_event(offender, event, score_factors, attackscore_history_kwargs):
    from_address = Config.objects.get(key='notifications_email_address_from').value
    to_address = [Config.objects.get(key='notifications_email_address_to').value]
    subject = 'Suggested action: Offender %s/%i - score %i' % (
        offender.address,
        offender.cidr,
        attackscore_history_kwargs['total_score'],
    )
    message = "Events from ArcSight have exceeded the threshold in banhammer-ng.\n\n"
    message += "More info: %s/blacklist/offender/%s\n\n" % (
        settings.HTTP_SERVER,
        offender.id
    )
    
    # Event
    message += "Event:\n"
    message += "* eventId: %i\n" % event.eventId
    message += "* Rule name: %s\n" % event.rulename
    message += "* Severity: %s\n" % event.severity
    message += "* attackerAddress: %s\n" % event.attackerAddress
    
    # Keep only relevant fields
    fields = {}
    for i in event.__dict__:
        if i not in ['_state', 'id', 'eventId', 'rulename', 'severity', 'attackerAddress']:
            if event.__dict__[i] != None:
                fields[i] = event.__dict__[i]
    
    for i in fields:
        message += "* %s: %s\n" % (i, fields[i])
        
    message += "\n"
    
    # Score
    message += "Score %s:\n" % attackscore_history_kwargs['total_score']
    for i in attackscore_history_kwargs:
        if i not in ['total', 'offender', 'event'] and '_score' not in i:
            message += "* %s: %s * %s = %s\n" % (
                i,
                attackscore_history_kwargs[i],
                score_factors[i],
                attackscore_history_kwargs[i+'_score'],
            )
    
    message += "\n"
    
    message += "Powered by RTBH-ng"
    
    send_mail(subject, message, from_address, to_address, fail_silently=False)

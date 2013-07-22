from django.core.mail import send_mail

import subprocess
import shlex

from BanHammer.blacklist.models import Config
from BanHammer import settings

def email_enabled():
    return bool(Config.objects.get(key="notifications_email_enable").value)

def irc_enabled():
    return bool(Config.objects.get(key="notifications_irc_enable").value)

def send_irc_new_event(offender, event, score_factors, attackscore_history_kwargs):
    message = irc_new_event_data(offender, event, score_factors, attackscore_history_kwargs)
    subprocess.Popen(shlex.split(settings.MANAGEMENT_FOLDER+'/rtbh-ng_notify '+message))

def send_email_new_event(offender, event, score_factors, attackscore_history_kwargs):
    data = email_new_event_data(offender, event, score_factors, attackscore_history_kwargs)
    send_mail(fail_silently=False, **data)

def irc_new_event_data(offender, event, score_factors, attackscore_history_kwargs):
    message = "BanHammer-ng:"
    message += " offender "+offender.address
    message += " with score %i." % attackscore_history_kwargs['total_score']
    message += " Last event %s." % event.rulename
    message += " More info: %s/blacklist/offender/%s\n\n" % (
        settings.HTTP_SERVER,
        offender.id
    )
    return message

def email_new_event_data(offender, event, score_factors, attackscore_history_kwargs):
    data = {}
    data['from_email'] = Config.objects.get(key='notifications_email_address_from').value
    data['recipient_list'] = [Config.objects.get(key='notifications_email_address_to').value]
    data['subject']= 'Suggested action: Offender %s/%i - score %i' % (
        offender.address,
        offender.cidr,
        attackscore_history_kwargs['total_score'],
    )
    data['message'] = "Events from ArcSight have exceeded the threshold in banhammer-ng.\n\n"
    data['message'] += "More info: %s/blacklist/offender/%s\n\n" % (
        settings.HTTP_SERVER,
        offender.id
    )
    
    # Event
    data['message'] += "Event:\n"
    data['message'] += "* eventId: %i\n" % event.eventId
    data['message'] += "* Rule name: %s\n" % event.rulename
    data['message'] += "* Severity: %s\n" % event.severity
    data['message'] += "* attackerAddress: %s\n" % event.attackerAddress
    
    # Keep only relevant fields
    fields = {}
    for i in event.__dict__:
        if i not in ['_state', 'id', 'eventId', 'rulename', 'severity', 'attackerAddress']:
            if event.__dict__[i] != None:
                fields[i] = event.__dict__[i]
    
    for i in fields:
        data['message'] += "* %s: %s\n" % (i, fields[i])
        
    data['message'] += "\n"
    
    # Score
    data['message'] += "Score %s:\n" % attackscore_history_kwargs['total_score']
    for i in attackscore_history_kwargs:
        if i not in ['total', 'offender', 'event'] and '_score' not in i:
            data['message'] += "* %s: %s * %s = %s\n" % (
                i,
                attackscore_history_kwargs[i],
                score_factors[i],
                attackscore_history_kwargs[i+'_score'],
            )
    
    data['message'] += "\n"
    
    data['message'] += "Powered by RTBH-ng"
    
    return data

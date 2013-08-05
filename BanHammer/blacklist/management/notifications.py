from django.core.mail import send_mail

import subprocess
import shlex

from BanHammer.blacklist.models import Config, ZLBBlacklist
from BanHammer import settings

def email_enabled():
    return bool(int(Config.objects.get(key="notifications_email_enable").value))

def irc_enabled():
    return bool(int(Config.objects.get(key="notifications_irc_enable").value))

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
    message += " More info: %s/offender/%s\n\n" % (
        settings.HTTP_SERVER,
        offender.address
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
    data['message'] += "More info: %s/offender/%s\n\n" % (
        settings.HTTP_SERVER,
        offender.address
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

def send_email_new_blacklist(blacklist, offender):
    data = email_new_blacklist_data(blacklist, offender)
    send_mail(fail_silently=False, **data)

def email_new_blacklist_data(blacklist, offender):
    data = {}
    data['from_email'] = Config.objects.get(key='notifications_email_address_from').value
    data['recipient_list'] = [Config.objects.get(key='notifications_email_address_to').value]
    data['subject']= 'New %s blacklist: Offender %s/%i' % (
        blacklist.type,
        offender.address,
        offender.cidr,
    )
    
    data['message'] = "%s has added a new %s blacklist on BanHammer-ng.\n\n" % (
        blacklist.reporter, blacklist.type)
    
    data['message'] += "More info: %s/offender/%s\n\n" % (
        settings.HTTP_SERVER,
        offender.id,
    )
    
    data['message'] += "Blacklist details:\n"
    data['message'] += "* Type: %s\n" % blacklist.type
    data['message'] += "* Start Time (UTC): %s\n" % blacklist.start_date
    data['message'] += "* Expiration (UTC): %s\n" % blacklist.end_date
    data['message'] += "* Reporter: %s\n" % blacklist.reporter
    data['message'] += "* Comment: %s\n" % blacklist.comment
    if blacklist.bug_number:
        data['message'] += "* Bug number: %s\n" % blacklist.bug_number
    if blacklist.type in ['zlb_redirect', 'zlb_block']:
        zlb_blacklist_o = ZLBBlacklist.objects.filter(blacklist=blacklist)
        data['message'] += "* Virtual Servers :"
        for i in zlb_blacklist_o:
            data['message'] += "%s (%s)," % (i.virtual_server_name, i.zlb_name)
    data['message'] += "\n\n"
    
    data['message'] += "Offender details:\n"
    data['message'] += "* address: %s\n" % offender.address
    data['message'] += "* cidr: %s\n" % offender.cidr
    if offender.hostname:
        data['message'] += "* hostname: %s\n" % offender.hostname
    if offender.asn:
        data['message'] += "* ASN: %s\n" % offender.asn
    
    data['message'] += "\n\n"
    
    data['message'] += "Powered by RTBH-ng"
    
    return data
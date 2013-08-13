from BanHammer.blacklist.models import Config, ZLBBlacklist
from BanHammer import settings

def irc_new_event_data(offender_d, event_d, attackscore_history_d):
    message = "BanHammer-ng: Event threshold:"
    message += " offender %s" % offender_d['address']
    message += " with score %i." % offender_d['score']
    message += " Last event %s." % event_d['rulename']
    message += " More info: %s/offender/%s\n\n" % (
        settings.HTTP_SERVER,
        offender_d['address']
    )
    return message

def email_event_event(event_d):
    """Event part of a new/deleted event email"""
    output = "Event:\n"
    output += "* eventId: %i\n" % event_d['eventId']
    output += "* Rule name: %s\n" % event_d['rulename']
    output += "* Severity: %s\n" % event_d['severity']
    output += "* attackerAddress: %s\n" % event_d['attackerAddress']
    
    # Keep only relevant fields
    fields = {}
    for i in event_d:
        if i not in ['_state', 'id', 'eventId', 'rulename', 'severity', 'attackerAddress']:
            if event_d[i] != None:
                fields[i] = event_d[i]
    
    for i in fields:
        output += "* %s: %s\n" % (i, fields[i])
        
    output += "\n"
    return output

def email_event_score(attackscore_history_d, score_factors_d):
    """Score part of a new/deleted event email"""
    output = "Score %s:\n" % attackscore_history_d['total_score']
    for i in attackscore_history_d:
        if i not in ['total', 'offender', 'event'] and '_score' not in i:
            output += "* %s: %s * %s = %s\n" % (
                i,
                attackscore_history_d[i],
                score_factors_d[i],
                attackscore_history_d[i+'_score'],
            )
    
    output += "\n"
    return output

def email_new_event_data(offender_d, event_d, score_factors_d, attackscore_history_d):
    data = {}
    data['from_email'] = Config.objects.get(key='notifications_email_address_from').value
    data['recipient_list'] = [Config.objects.get(key='notifications_email_address_to').value]
    data['subject']= '[BanHammer-ng] Event threshold: Offender %s/%i - score %i' % (
        offender_d['address'],
        offender_d['cidr'],
        offender_d['score'],
    )
    data['message'] = "Events from ArcSight have exceeded the threshold in banhammer-ng.\n\n"
    data['message'] += "More info: %s/offender/%s\n\n" % (
        settings.HTTP_SERVER,
        offender_d['address']
    )
    
    data['message'] += email_event_event(event_d)
    data['message'] += email_event_score(attackscore_history_d, score_factors_d)
    
    data['message'] += "Powered by RTBH-ng"
    
    return data

def irc_delete_event_data(event_d, reporter):
    message = "BanHammer-ng: Event deleted by %s:" % reporter
    message += " %s from %s" % (event_d['rulename'], event_d['attackerAddress'])
    return message

def email_delete_event_data(event_d, reporter):
    data = {}
    data['from_email'] = Config.objects.get(key='notifications_email_address_from').value
    data['recipient_list'] = [Config.objects.get(key='notifications_email_address_to').value]
    data['subject']= '[BanHammer-ng] Event deleted by %s: %s from %s' % (
        reporter,
        event_d['rulename'],
        event_d['attackerAddress'],
    )

    data['message'] += email_event_event(event_d)
    
    data['message'] += "Powered by RTBH-ng"
    
    return data

def irc_new_blacklist_data(blacklist_d, offender_d):
    message = "BanHammer-ng: New %s blacklist:" % blacklist_d['type']
    message += " Offender %s/%s," % (offender_d['address'], offender_d['cidr'])
    message += " added by %s." % blacklist_d['reporter']
    message += " More info: %s/offender/%s\n\n" % (
        settings.HTTP_SERVER,
        offender_d['id'],
    )
    return message

def email_blacklist_blacklist(blacklist_d):
    """Blacklist part of a new/deleted blacklist email"""
    output = "Blacklist details:\n"
    output += "* Type: %s\n" % blacklist_d['type']
    output += "* Start Time (UTC): %s\n" % blacklist_d['start_date']
    output += "* Expiration (UTC): %s\n" % blacklist_d['end_date']
    output += "* Reporter: %s\n" % blacklist_d['reporter']
    output += "* Comment: %s\n" % blacklist_d['comment']
    if blacklist_d['bug_number']:
        output += "* Bug number: %s\n" % blacklist_d['bug_number']
    if blacklist_d['type'] in ['zlb_redirect', 'zlb_block']:
        zlb_blacklist_o = ZLBBlacklist.objects.filter(blacklist_id=blacklist_d['id'])
        output += "* Virtual Servers :"
        for i in zlb_blacklist_o:
            output += "%s (%s)," % (i.virtual_server_name, i.zlb_name)
    output += "\n\n"
    return output

def email_blacklist_offender(offender_d):
    """Offender part of a new/deleted blacklist email"""
    output = "Offender details:\n"
    output += "* address: %s\n" % offender_d['address']
    output += "* cidr: %s\n" % offender_d['cidr']
    output += "* score: %s\n" % offender_d['score']
    if offender_d['hostname']:
        output += "* hostname: %s\n" % offender_d['hostname']
    if offender_d['asn']:
        output += "* ASN: %s\n" % offender_d['asn']
    output += "* created_date: %s\n" % offender_d['created_date']
    output += "* updated_date: %s\n" % offender_d['updated_date']
    output += "\n\n"
    return output

def email_new_blacklist_data(blacklist_d, offender_d):
    data = {}
    data['from_email'] = Config.objects.get(key='notifications_email_address_from').value
    data['recipient_list'] = [Config.objects.get(key='notifications_email_address_to').value]
    data['subject']= '[BanHammer-ng] New %s blacklist: Offender %s/%i, added by %s' % (
        blacklist_d['type'],
        offender_d['address'],
        offender_d['cidr'],
        blacklist_d['reporter'],
    )
    
    data['message'] = "More info: %s/offender/%s\n\n" % (
        settings.HTTP_SERVER,
        offender_d['id'],
    )
    
    data['message'] += email_blacklist_blacklist(blacklist_d)
    data['message'] += email_blacklist_offender(offender_d)
    
    data['message'] += "Powered by RTBH-ng"
    
    return data

def irc_delete_blacklist_data(blacklist_d, offender_d, reporter):
    message = "BanHammer-ng: %s deleted %s blacklist for %s/%s." % (
        reporter,
        blacklist_d['type'],
        offender_d['address'],
        offender_d['cidr'],
    )
    message += " More info: %s/offender/%s\n\n" % (
        settings.HTTP_SERVER,
        offender_d['id'],
    )
    return message

def email_delete_blacklist_data(blacklist_d, offender_d, reporter):
    data = {}
    data['from_email'] = Config.objects.get(key='notifications_email_address_from').value
    data['recipient_list'] = [Config.objects.get(key='notifications_email_address_to').value]
    data['subject']= '[BanHammer-ng] %s deleted %s blacklist for %s/%s' % (
        reporter,
        blacklist_d['type'],
        offender_d['address'],
        offender_d['cidr'],
    )
    
    data['message'] = "More info: %s/offender/%s\n\n" % (
        settings.HTTP_SERVER,
        offender_d['id'],
    )
    
    data['message'] += email_blacklist_blacklist(blacklist_d)
    data['message'] += email_blacklist_offender(offender_d)
    
    data['message'] += "Powered by RTBH-ng"
    
    return data

def irc_new_ip_whitelist_data(whitelistip_d):
    message = "BanHammer-ng: New IP Whitelist: %s/%s, added by %s." % (
        whitelistip_d['address'],
        whitelistip_d['cidr'],
        whitelistip_d['reporter'],
        
    )
    message += " More info: %s/whitelistip\n\n" % (
        settings.HTTP_SERVER,
    )
    return message

def email_ip_whitelist_whitelist(whitelistip_d):
    """IP Whitelist part of a new/deleted ip whitelist email"""
    output = "IP Whitelist:\n"
    output += "* address: %s\n" % whitelistip_d['address']
    output += "* cidr: %s\n" % whitelistip_d['cidr']
    output += "* reporter: %s\n" % whitelistip_d['reporter']
    output += "* comment: %s\n" % whitelistip_d['comment']
    output += "* created_date: %s\n" % whitelistip_d['created_date']
    output += "* updated_date: %s\n" % whitelistip_d['updated_date']
    output += "\n\n"
    return output

def email_new_ip_whitelist_data(whitelistip_d):
    data = {}
    data['from_email'] = Config.objects.get(key='notifications_email_address_from').value
    data['recipient_list'] = [Config.objects.get(key='notifications_email_address_to').value]
    data['subject']= '[BanHammer-ng] New IP Whitelist: %s/%s, added by %s' % (
        whitelistip_d['address'],
        whitelistip_d['cidr'],
        whitelistip_d['reporter']
    )
    
    data['message'] = "More info: %s/whitelistip\n\n" % (
        settings.HTTP_SERVER,
    )
    
    data['message'] += email_ip_whitelist_whitelist(whitelistip_d)
    
    data['message'] += "Powered by RTBH-ng"
    
    return data

def irc_delete_ip_whitelist_data(whitelistip_d, reporter):
    message = "BanHammer-ng: %s deleted %s/%s from the IP Whitelist." % (
        reporter,
        whitelistip_d['address'],
        whitelistip_d['cidr'],
        
    )
    message += " More info: %s/whitelistip\n\n" % (
        settings.HTTP_SERVER,
    )
    return message

def email_delete_ip_whitelist_data(whitelistip_d, reporter):
    data = {}
    data['from_email'] = Config.objects.get(key='notifications_email_address_from').value
    data['recipient_list'] = [Config.objects.get(key='notifications_email_address_to').value]
    data['subject']= '[BanHammer-ng] %s deleted %s/%s from the IP Whitelist' % (
        reporter,
        whitelistip_d['address'],
        whitelistip_d['cidr']
    )
    
    data['message'] = "More info: %s/whitelistip\n\n" % (
        settings.HTTP_SERVER,
    )
    
    data['message'] += email_ip_whitelist_whitelist(whitelistip_d)
    
    data['message'] += "Powered by RTBH-ng"
    
    return data

def irc_delete_offender_data(offender_d, reporter):
    message = "BanHammer-ng: %s deleted %s/%s offender" % (
        reporter,
        offender_d['address'],
        offender_d['cidr'],
    )
    return message

def email_delete_offender_data(offender_d, reporter):
    data = {}
    data['from_email'] = Config.objects.get(key='notifications_email_address_from').value
    data['recipient_list'] = [Config.objects.get(key='notifications_email_address_to').value]
    data['subject']= '[BanHammer-ng] %s deleted %s/%s offender' % (
        reporter,
        offender_d['address'],
        offender_d['cidr']
    )
    
    data['message'] = email_blacklist_offender(offender_d)
    
    data['message'] += "Powered by RTBH-ng"
    
    return data

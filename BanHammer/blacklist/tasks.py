from celery.task import task

from BanHammer.blacklist import models
from BanHammer.blacklist.management import zeus
from BanHammer.blacklist.management import notifications
from BanHammer import settings

from django.core.mail import send_mail

import subprocess
import shlex
import datetime
import logging
import hashlib

@task(name="BanHammer.blacklist.tasks.update_zlb")
def update_zlb(id):
    zlb_m = models.ZLB.objects.get(id=id)
    zlb_m.updating = True
    zlb_m.save()
    logging.info('zlb: %s' % zlb_m.name)

    if not settings.TESTING_ENV:
        zlb = models.ZLB.objects.get(id=id)
        z = zeus.ZLB(zlb.hostname, zlb.login, zlb.password)
        
        # Empty the db
        models.ZLBProtection.objects.all().delete()
        models.ZLBRule.objects.all().delete()
        models.ZLBVirtualServerRule.objects.all().delete()
        models.ZLBVirtualServerProtection.objects.all().delete()
        models.ZLBVirtualServer.objects.all().delete()
        
        logging.info('Updating Protection Classes')
        z.connect('Catalog.Protection')
        protectionnames = list(z.conn.getProtectionNames())
        allowed_addresses_list = list(z.conn.getAllowedAddresses(protectionnames))
        banned_addresses_list = list(z.conn.getBannedAddresses(protectionnames))
        debug_list = list(z.conn.getDebug(protectionnames))
        enabled_list = list(z.conn.getEnabled(protectionnames))
        note_list = list(z.conn.getNote(protectionnames))
        testing_list = list(z.conn.getTesting(protectionnames))
        
        for rule_index in range(len(protectionnames)):
            allowed_addresses = []
            for addr in allowed_addresses_list[rule_index]:
                allowed_addresses.append(str(addr))
            allowed_addresses = ', '.join(allowed_addresses)
                
            banned_addresses = []
            for addr in banned_addresses_list[rule_index]:
                banned_addresses.append(str(addr))
            banned_addresses = ', '.join(banned_addresses)
            
            pr = models.ZLBProtection(
                zlb_id=zlb.id,
                name=protectionnames[rule_index],
                allowed_addresses=allowed_addresses,
                banned_addresses=banned_addresses,
                debug=debug_list[rule_index],
                enabled=enabled_list[rule_index],
                note=note_list[rule_index],
                testing=testing_list[rule_index],
            )
            pr.save()
    
        logging.info('Updating TrafficScript Rules')
        z.connect('Catalog.Rule')    
        rulenames = list(z.conn.getRuleNames())
        ruledetails = list(z.conn.getRuleDetails(rulenames))
    
        for rule_index in range(len(rulenames)):
            rule = models.ZLBRule(
                zlb_id=zlb.id,
                name=rulenames[rule_index],
                rule_text=ruledetails[rule_index].rule_text,
                rule_notes=ruledetails[rule_index].rule_notes,
            )
            rule.save()
        
        logging.info('Updating Virtual Servers')
        z.connect('VirtualServer')
        logging.info("Virtual Servers - SOAP")
        virtualservernames = list(z.conn.getVirtualServerNames())
        enabled_list = list(z.conn.getEnabled(virtualservernames))
        basicinfo_list = list(z.conn.getBasicInfo(virtualservernames))
        rules_list = list(z.conn.getRules(virtualservernames))
        protection_list = list(z.conn.getProtection(virtualservernames))
        
        logging.info("Virtual Servers - DB")
        for vs_index in range(len(virtualservernames)):
            vs_name = virtualservernames[vs_index]
            vs = models.ZLBVirtualServer(
                zlb_id=zlb.id,
                name=vs_name,
                enabled=enabled_list[vs_index],
                port=basicinfo_list[vs_index].port,
                protocol=basicinfo_list[vs_index].protocol,
                default_pool=basicinfo_list[vs_index].default_pool,
            )
            vs.save()
    
            for rule in rules_list[vs_index]:
                rule_o = models.ZLBRule.objects.get(name=rule.name, zlb_id=zlb.id)
                vs_rule = models.ZLBVirtualServerRule(
                    zlb_id=zlb.id,
                    virtualserver=vs,
                    rule=rule_o,
                    enabled=rule.enabled,
                    run_frequency=str(rule.run_frequency),
                )
                vs_rule.save()
        
            protection = protection_list[vs_index]
            if protection:
                pr_o = models.ZLBProtection.objects.get(name=protection, zlb_id=zlb.id)
                vs_pr = models.ZLBVirtualServerProtection(
                    zlb_id=zlb.id,
                    virtualserver=vs,
                    protection=pr_o,
                )
                vs_pr.save()
                
                if protection != 'banned-'+vs_name:
                    try:
                        pref = models.ZLBVirtualServerPref.objects.get(zlb_id=zlb.id, vs_name=vs_name)
                        pref.other_protection = True
                        pref.save()
                    except:
                        pref = models.ZLBVirtualServerPref(
                            zlb=zlb,
                            vs_name=vs_name,
                            confirm=False,
                            favorite=False,
                            other_protection=True,
                        )
                        pref.save()
                else:
                    try:
                        pref = models.ZLBVirtualServerPref.objects.get(zlb_id=zlb.id, vs_name=vs_name)
                        pref.other_protection = False
                        pref.save()
                    except:
                        pass
        
        zlb_m.updating = False
        zlb_m.save()
    else:
        logging.warning('Testing mode, zlb not updated')

def _create_and_attach_protection(z, virtual_server_name, networks, class_name):
    z.connect('Catalog.Protection')
    try:
        z.conn.addProtection([class_name])
    except:
        # Protection already exists
        pass
    
    z.conn.setEnabled([class_name], [1])
    z.conn.addBannedAddresses([class_name], [networks])
    z.conn.setNote([class_name], ['Managed by BanHammer-ng, do not edit it.'])

    # Associate the class with the virtual server
    z.connect('VirtualServer')
    z.conn.setProtection([virtual_server_name], [class_name])

def _zlb_find_networks_blacklist(type, virtual_server_name, zlb_id):
    blacklists = models.ZLBBlacklist.objects.filter(virtual_server_name=virtual_server_name, zlb_id=zlb_id)
    networks = []
    secrets = []
    block_captcha = []
    for blacklist in blacklists:
        blacklist = blacklist.blacklist
        if blacklist.type == type:
            offender = blacklist.offender
            block_captcha.append(str(blacklist.block_captcha))
            secrets.append(hashlib.sha256(settings.SALT+str(blacklist.id)).hexdigest())
            if offender.cidr != 24 or offender.cidr != 128:
                networks.append("%s/%s" % (offender.address, offender.cidr))
            else:
                networks.append(offender.address)
    return (networks, secrets, block_captcha)

@task(name="BanHammer.blacklist.tasks.update_protection")
def update_protection(zlb_id, virtual_server_name):
    logging.info("zlb_id: %s" % zlb_id)
    logging.info("virtual_server_name: %s" % virtual_server_name)
    if not settings.TESTING_ENV:
        (networks, _, _) = _zlb_find_networks_blacklist('zlb_block', virtual_server_name, zlb_id)
        logging.info("networks: %s" % str(networks))
        
        class_name = 'banned-%s' % virtual_server_name
        zlb = models.ZLB.objects.get(id=zlb_id)
        z = zeus.ZLB(zlb.hostname, zlb.login, zlb.password)
        z.connect('VirtualServer')
        
        # A virtual server can only have one protection class
        class_name_current = z.conn.getProtection([virtual_server_name])[0]
        if class_name_current:
            z.connect('Catalog.Protection')
            # Detach the current rule
            note = z.conn.getNote([class_name_current])[0]
            note += "\nDetached from %s on %s by BanHammer-ng" % (virtual_server_name,
                                                                  str(datetime.datetime.now()))
            z.conn.setNote([class_name_current], [note])
            z.connect('VirtualServer')
            z.conn.setProtection([virtual_server_name], [''])
            _create_and_attach_protection(z, virtual_server_name, networks, class_name)
        else:
                _create_and_attach_protection(z, virtual_server_name, networks, class_name)
    else:
        logging.warning("Testing mode, protection class not updated")

@task(name="BanHammer.blacklist.tasks.update_protection_delete")
def update_protection_delete(zlb_id, virtual_server_name, offender=None, offender_ip=None, offender_cidr=None):
    logging.info("zlb_id: %s" % zlb_id)
    logging.info("virtual_server_name: %s" % virtual_server_name)
    
    if not settings.TESTING_ENV:
        if offender:
            networks = ["%s/%s" % (offender.address, offender.cidr)]
        else:
            networks = ["%s/%s" % (offender_ip, offender_cidr)]
        logging.info("networks: %s" % str(networks))
        
        class_name = 'banned-%s' % virtual_server_name
        zlb = models.ZLB.objects.get(id=zlb_id)
        z = zeus.ZLB(zlb.hostname, zlb.login, zlb.password)
        z.connect('VirtualServer')
        
        # A virtual server can only have one protection class
        class_name_current = z.conn.getProtection([virtual_server_name])[0]
        z.connect('Catalog.Protection')
        try:
            z.conn.removeBannedAddresses([class_name_current], [networks])
        except:
            logging.error("%s on %s protection class was already removed" % ((str(networks),
                                                                          class_name_current,)))
    else:
        logging.warning("Testing mode, protection class not deleted")

def _get_rule_content(networks, secrets, blocking):
    url_redirection = models.Config.objects.get(key='zlb_redirection_url')
    url_redirection = url_redirection.value
    url_blocking_redirection = models.Config.objects.get(key='redirect_block_url')
    url_blocking_redirection = url_blocking_redirection.value

    content = "# This script redirect attacker IPs to the BanHammer-ng captive portal\n\n"
    content += "$networks = ['"+"','".join(networks)+"'];\n"
    content += "$secrets = "+str(secrets)+";\n"
    content += "$blocking = "+str(blocking)+";\n"
    content += "$ip = request.getRemoteIP();\n\n"
    
    content += "for($i=0; $i < array.length($networks); $i++) {\n"
    content += "if (string.ipmaskmatch($ip, $networks[$i])) {\n"
    content += "$query = http.getQueryString();\n"
    content += "$cookie = http.getCookie('banhammer');\n"
    content += "$end_url = http.getRawURL();\n"
    content += "$host = http.getHeader('Host');\n"
    content += "$query = http.getQueryString();\n"
    content += "if (ssl.isSSL()) {\n"
    content += "$protocol = 'https://';\n"
    content += "}\n"
    content += "else {\n"
    content += "$protocol = 'http://';\n"
    content += '}\n'
    content += '$url = $protocol.$host.$end_url;\n'
    content += "if ($blocking[$i] != '0' && sys.time() <= $blocking[$i]) {\n"
    content += "http.redirect('"+url_blocking_redirection+"');\n"
    content += '}\n'
    content += 'else {\n'
    content += 'if(string.endsWith($query, $secrets[$i])) {\n'
    content += "http.setResponseCookie('banhammer', $secrets[$i]);\n"
    content += '}\n'
    content += 'else {\n'
    content += 'if ($cookie != $secrets[$i]) {\n'
    content += "http.redirect('"+url_redirection+"?url='.$url);\n"
    content += '}\n'
    content += '}\n'
    content += '}\n'
    content += '}\n'
    content += '}\n'
    
    return content

@task(name="BanHammer.blacklist.tasks.update_rule")
def update_rule(zlb_id, virtual_server_name, blocking_net=None):
    logging.info("zlb_id: %s" % zlb_id)
    logging.info("virtual_server_name: %s" % virtual_server_name)
    if not settings.TESTING_ENV:
        (networks, secrets, blocking) = _zlb_find_networks_blacklist('zlb_redirect', virtual_server_name, zlb_id)
        logging.info("networks: %s" % str(networks))
        
        logging.info("blocking: %s" % str(blocking))
        
        rule_name = 'banhammer-redirected-%s' % virtual_server_name
        zlb = models.ZLB.objects.get(id=zlb_id)
        z = zeus.ZLB(zlb.hostname, zlb.login, zlb.password)
        
        rule = _get_rule_content(networks, secrets, blocking)
        logging.info(rule)
        
        z.connect('Catalog.Rule')
        try:
            z.conn.addRule([rule_name], [rule])
        except:
            # The rule already exists
            z.conn.setRuleText([rule_name], [rule])
        z.conn.setRuleNotes([rule_name], ["Managed by BanHammer-ng, do not edit it."])
        
        z.connect('VirtualServer')
        z.conn.addRules([virtual_server_name], [[{'enabled': 1, 'name': rule_name, 'run_frequency': 'run_every'}]]) 
    else:
        logging.warning("Testing mode, rule not updated")

@task(name="BanHammer.blacklist.tasks.delete_offender")
def delete_offender(offender_ip, offender_cidr, protections_vs, redirections_vs):
    logging.info("offender: %s/%s" % (offender_ip, offender_cidr))
    logging.info("protection_vs: %s" % str(protections_vs))
    logging.info("redirections_vs: %s" % str(redirections_vs))
    if not settings.TESTING_ENV:
        logging.info("Updating protection classes")
        for (zlb_id, virtual_server_name) in protections_vs:
            update_protection_delete(
                zlb_id, virtual_server_name, offender_ip=offender_ip, offender_cidr=offender_cidr)
        logging.info("Updating TrafficScript rules")
        for (zlb_id, virtual_server_name) in redirections_vs:
            update_rule(zlb_id, virtual_server_name)
    else:
        logging.warning("Testing mode, offender not deleted")

@task(name="BanHammer.blacklist.tasks.notification_new_event")
def notification_new_event(offender_d, event_d, score_factors_d, attackscore_history_d):
    # Email
    if bool(int(models.Config.objects.get(key="notifications_email_new_event_enable").value)):
        thresholds = models.Config.objects.get(key="notifications_email_events_threshold").value
        for threshold in thresholds.split(' '):
            threshold = int(threshold)
            score_after = offender_d['score']
            score_before = score_after - attackscore_history_d['total_score']
            if score_before < threshold and threshold <= score_after:
                data = notifications.email_new_event_data(
                    offender_d,
                    event_d,
                    score_factors_d,
                    attackscore_history_d)
                send_mail(fail_silently=False, **data)
    # IRC
    if bool(int(models.Config.objects.get(key="notifications_irc_new_event_enable").value)):
        thresholds = models.Config.objects.get(key="notifications_irc_events_threshold").value
        for threshold in thresholds.split(' '):
            threshold= int(threshold)
            score_after = offender_d['score']
            score_before = score_after - attackscore_history_d['total_score']
            if score_before < threshold and threshold <= score_after:
                message = notifications.irc_new_event_data(
                    offender_d,
                    event_d,
                    attackscore_history_d)
                subprocess.Popen(shlex.split(settings.MANAGEMENT_FOLDER+'/rtbh-ng_notify '+message))

@task(name="BanHammer.blacklist.tasks.notification_delete_event")
def notification_delete_event(event_d, reporter):
    # Email
    if bool(int(models.Config.objects.get(key="notifications_email_delete_event_enable").value)):
        data = notifications.email_delete_event_data(
            event_d,
            reporter)
        send_mail(fail_silently=False, **data)
    # IRC
    if bool(int(models.Config.objects.get(key="notifications_irc_delete_event_enable").value)):
        message = notifications.irc_delete_event_data(
            event_d,
            reporter)
        subprocess.Popen(shlex.split(settings.MANAGEMENT_FOLDER+'/rtbh-ng_notify '+message))

@task(name="BanHammer.blacklist.tasks.notification_add_blacklist")
def notification_add_blacklist(blacklist_d, offender_d):
    # Email
    if bool(int(models.Config.objects.get(key="notifications_email_new_blacklist_enable").value)):
        data = notifications.email_new_blacklist_data(
            blacklist_d,
            offender_d)
        send_mail(fail_silently=False, **data)
    # IRC
    if bool(int(models.Config.objects.get(key="notifications_irc_new_blacklist_enable").value)):
        message = notifications.irc_new_blacklist_data(
            blacklist_d,
            offender_d)
        subprocess.Popen(shlex.split(settings.MANAGEMENT_FOLDER+'/rtbh-ng_notify '+message))

@task(name="BanHammer.blacklist.tasks.notification_delete_blacklist")
def notification_delete_blacklist(blacklist_d, offender_d, reporter):
    # Email
    if bool(int(models.Config.objects.get(key="notifications_email_delete_blacklist_enable").value)):
        data = notifications.email_delete_blacklist_data(
            blacklist_d,
            offender_d,
            reporter)
        send_mail(fail_silently=False, **data)
    # IRC
    if bool(int(models.Config.objects.get(key="notifications_irc_delete_blacklist_enable").value)):
        message = notifications.irc_delete_blacklist_data(
            blacklist_d,
            offender_d,
            reporter)
        subprocess.Popen(shlex.split(settings.MANAGEMENT_FOLDER+'/rtbh-ng_notify '+message))

@task(name="BanHammer.blacklist.tasks.notification_add_ip_whitelist")
def notification_add_ip_whitelist(whitelistip_d):
    # Email
    if bool(int(models.Config.objects.get(key="notifications_email_new_ip_whitelist_enable").value)):
        data = notifications.email_new_ip_whitelist_data(whitelistip_d)
        send_mail(fail_silently=False, **data)
    # IRC
    if bool(int(models.Config.objects.get(key="notifications_irc_new_ip_whitelist_enable").value)):
        message = notifications.irc_new_ip_whitelist_data(whitelistip_d)
        subprocess.Popen(shlex.split(settings.MANAGEMENT_FOLDER+'/rtbh-ng_notify '+message))

@task(name="BanHammer.blacklist.tasks.notification_delete_ip_whitelist")
def notification_delete_ip_whitelist(whitelistip_d, reporter):
    # Email
    if bool(int(models.Config.objects.get(key="notifications_email_delete_ip_whitelist_enable").value)):
        data = notifications.email_delete_ip_whitelist_data(whitelistip_d, reporter)
        send_mail(fail_silently=False, **data)
    # IRC
    if bool(int(models.Config.objects.get(key="notifications_irc_delete_ip_whitelist_enable").value)):
        message = notifications.irc_delete_ip_whitelist_data(whitelistip_d, reporter)
        subprocess.Popen(shlex.split(settings.MANAGEMENT_FOLDER+'/rtbh-ng_notify '+message))

@task(name="BanHammer.blacklist.tasks.notification_delete_offender")
def notification_delete_offender(offender_d, reporter):
    # Email
    if bool(int(models.Config.objects.get(key="notifications_email_delete_offender_enable").value)):
        data = notifications.email_delete_offender_data(offender_d, reporter)
        send_mail(fail_silently=False, **data)
    # IRC
    if bool(int(models.Config.objects.get(key="notifications_irc_delete_offender_enable").value)):
        message = notifications.irc_delete_offender_data(offender_d, reporter)
        subprocess.Popen(shlex.split(settings.MANAGEMENT_FOLDER+'/rtbh-ng_notify '+message))

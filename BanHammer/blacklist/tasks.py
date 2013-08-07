from celery.task import task

from BanHammer.blacklist import models
from BanHammer.blacklist.management import zeus
from BanHammer.blacklist.management import notifications

import datetime
import logging

@task(name="BanHammer.blacklist.tasks.update_zlb")
def update_zlb(id):
    zlb_m = models.ZLB.objects.get(id=id)
    zlb_m.updating = True
    zlb_m.save()
    logging.info('zlb: %s' % zlb_m.name)

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

@task(name="BanHammer.blacklist.tasks.add_blacklist_notification",
      default_retry_delay=60,
      max_retries=3)
def add_blacklist_notification(blacklist, offender):
    try:
        if notifications.email_enabled():
            notifications.send_email_new_blacklist(blacklist, offender)
    except Exception, exc:
        raise update_protection.retry(exc=exc, countdown=5)

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

def _zlb_find_networks(type, virtual_server_name, zlb_id):
    blacklists = models.ZLBBlacklist.objects.filter(virtual_server_name=virtual_server_name, zlb_id=zlb_id)
    networks = []
    for blacklist in blacklists:
        blacklist = blacklist.blacklist
        if blacklist.type == type:
            offender = blacklist.offender
            if offender.cidr != 24 or offender.cidr != 128:
                networks.append("%s/%s" % (offender.address, offender.cidr))
            else:
                networks.append(offender.address)
    return networks

@task(name="BanHammer.blacklist.tasks.update_protection")
def update_protection(zlb_id, virtual_server_name):
    logging.info("zlb_id: %s" % zlb_id)
    logging.info("virtual_server_name: %s" % virtual_server_name)
    networks = _zlb_find_networks('zlb_block', virtual_server_name, zlb_id)
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

@task(name="BanHammer.blacklist.tasks.update_protection_delete")
def update_protection_delete(zlb_id, virtual_server_name, offender=None, offender_ip=None, offender_cidr=None):
    logging.info("zlb_id: %s" % zlb_id)
    logging.info("virtual_server_name: %s" % virtual_server_name)
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

def _get_rule_content(networks):
    url_redirection = models.Config.objects.get(key='zlb_redirection_url')
    url_redirection = url_redirection.value
    
    content = '# This script redirect attacker IPs to the BanHammer-ng captive portal\n\n'
    content += '$networks = ["192.168.56.1/32"];\n'
    content += '$ip = request.getRemoteIP();\n\n'

    content += 'for($i=0; $i < array.length($networks); $i++) {\n'
    content += 'if (string.ipmaskmatch($ip, $networks[$i])) {\n'
    content += '# Enforce the redirection\n'
    content += 'http.redirect("%s");\n' % url_redirection
    content += '}\n'
    content += '}\n'
    
    return content

@task(name="BanHammer.blacklist.tasks.update_rule")
def update_rule(zlb_id, virtual_server_name):
    logging.info("zlb_id: %s" % zlb_id)
    logging.info("virtual_server_name: %s" % virtual_server_name)
    networks = _zlb_find_networks('zlb_redirect', virtual_server_name, zlb_id)
    logging.info("networks: %s" % str(networks))
    
    rule_name = 'banhammer-redirected-%s' % virtual_server_name
    zlb = models.ZLB.objects.get(id=zlb_id)
    z = zeus.ZLB(zlb.hostname, zlb.login, zlb.password)
    
    rule = _get_rule_content(networks)
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

@task(name="BanHammer.blacklist.tasks.delete_offender")
def delete_offender(offender_ip, offender_cidr, protections_vs, redirections_vs):
    logging.info("offender: %s/%s" % (offender_ip, offender_cidr))
    logging.info("Updating protection classes")
    for (zlb_id, virtual_server_name) in protections_vs:
        update_protection_delete(zlb_id, virtual_server_name,
                                 offender_ip=offender_ip, offender_cidr=offender_cidr)
    logging.info("Updating TrafficScript rules")
    for (zlb_id, virtual_server_name) in redirections_vs:
        update_rule(zlb_id, virtual_server_name)

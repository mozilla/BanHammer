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
    # Fill the db
    z.connect('Catalog.Protection')
    for rule_name in list(z.conn.getProtectionNames()):
        allowed_addresses = []
        for addr in list(z.conn.getAllowedAddresses([rule_name]))[0]:
            allowed_addresses.append(str(addr))
        allowed_addresses = ', '.join(allowed_addresses)
            
        banned_addresses = []
        for addr in list(z.conn.getBannedAddresses([rule_name]))[0]:
            banned_addresses.append(str(addr))
        banned_addresses = ', '.join(banned_addresses)
        
        debug = z.conn.getDebug([rule_name])[0]
        enabled = z.conn.getEnabled([rule_name])[0]
        note = z.conn.getNote([rule_name])[0]
        testing = z.conn.getTesting([rule_name])[0]
        pr = models.ZLBProtection(
            zlb_id=zlb.id,
            name=rule_name,
            allowed_addresses=allowed_addresses,
            banned_addresses=banned_addresses,
            debug=debug,
            enabled=enabled,
            note=note,
            testing=testing,
        )
        pr.save()
    
    logging.info('Updating TrafficScript Rules')
    z.connect('Catalog.Rule')
    for rule_name in list(z.conn.getRuleNames()):
        details = z.conn.getRuleDetails([rule_name])[0]
        rule_text = details.rule_text
        rule_notes = details.rule_notes
        rule = models.ZLBRule(
            zlb_id=zlb.id,
            name=rule_name,
            rule_text=rule_text,
            rule_notes=rule_notes,
        )
        rule.save()
    
    logging.info('Updating Virtual Servers')
    z.connect('VirtualServer')
    for vs_name in list(z.conn.getVirtualServerNames()):
        enabled = z.conn.getEnabled([vs_name])[0]
        basicInfo = z.conn.getBasicInfo([vs_name])[0]
        port = basicInfo.port
        protocol = basicInfo.protocol
        default_pool = basicInfo.default_pool
        vs = models.ZLBVirtualServer(
            zlb_id=zlb.id,
            name=vs_name,
            enabled=enabled,
            port=port,
            protocol=protocol,
            default_pool=default_pool,
        )
        vs.save()

        for rule in list(z.conn.getRules([vs_name]))[0]:
            rule_o = models.ZLBRule.objects.get(name=rule.name, zlb_id=zlb.id)
            enabled = rule.enabled
            run_frequency = str(rule.run_frequency)
            vs_rule = models.ZLBVirtualServerRule(
                zlb_id=zlb.id,
                virtualserver=vs,
                rule=rule_o,
                enabled=enabled,
                run_frequency=run_frequency,
            )
            vs_rule.save()
    
        for protection in z.conn.getProtection([vs_name]):
            if protection:
                pr_o = models.ZLBProtection.objects.get(name=protection, zlb_id=zlb.id)
                vs_pr = models.ZLBVirtualServerProtection(
                    zlb_id=zlb.id,
                    virtualserver=vs,
                    protection=pr_o,
                )
                vs_pr.save()
    
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
        enabled = z.conn.getEnabled([class_name_current])[0]
        logging.info("Enabled: %s" % str(enabled))
        # if the current class is enabled, add banned addresses to it
        if enabled:
            z.connect('Catalog.Protection')
            z.conn.addBannedAddresses([class_name_current], [networks])
        # if the current class is disabled, detach it from the virtual server
        else:
            # update note to say that it has been detached by banhammer-ng
            note = z.conn.getNote([class_name_current])[0]
            note += "\nDetached from %s on %s by BanHammer-ng" % (virtual_server_name,
                                                                  str(datetime.datetime.now()))
            z.conn.setNote([class_name_current], [note])
            z.connect('VirtualServer')
            z.conn.setProtection([virtual_server_name], [''])
            _create_and_attach_protection(z, virtual_server_name, networks, class_name)
    else:
            _create_and_attach_protection(z, virtual_server_name, networks, class_name)

@task(name="BanHammer.blacklist.tasks.update_rule")
def update_rule(zlb_id, virtual_server_name):
    logging.info("zlb_id: %s" % zlb_id)
    logging.info("virtual_server_name: %s" % virtual_server_name)
    networks = _zlb_find_networks('zlb_redirect', virtual_server_name, zlb_id)
    logging.info("networks: %s" % str(networks))
    
    rule_name = 'banhammer-redirected-%s' % virtual_server_name
    zlb = models.ZLB.objects.get(id=zlb_id)
    z = zeus.ZLB(zlb.hostname, zlb.login, zlb.password)
    
    # TODO: inject the good rule
    rule = "$ips = '%s';" % (''.join(networks))
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

from celery.task import task

from BanHammer.blacklist import models
from BanHammer.blacklist.management import zeus

import logging

@task(name="BanHammer.blacklist.tasks.update_zlb")
def update_zlb(id):
    zlb_m = models.ZLB.objects.get(id=id)
    zlb_m.updating = True
    zlb_m.save()

    zlb = models.ZLB.objects.get(id=id)
    z = zeus.ZLB(zlb.hostname, zlb.login, zlb.password)
    
    # Empty the db
    models.ZLBProtection.objects.all().delete()
    models.ZLBRule.objects.all().delete()
    models.ZLBVirtualServerRule.objects.all().delete()
    models.ZLBVirtualServerProtection.objects.all().delete()
    models.ZLBVirtualServer.objects.all().delete()
    
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

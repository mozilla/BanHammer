""" Derek Moore <dmoore@mozilla.com> 11/15/2010 """

from django.db import models
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode

import datetime
import netaddr

from BanHammer import settings

def uniquify(items):
    checked = []
    for i in items:
        if i['rulename'] not in checked:
            checked.append(i['rulename'])
    return checked

class Config(models.Model):
    key = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

class Offender(models.Model):
    address = models.CharField(max_length=39)
    cidr = models.IntegerField()
    hostname = models.CharField(max_length=255, null=True)
    asn = models.IntegerField(null=True)
    # Is it only a suggestion or a host that was actually blocked?
    suggestion = models.BooleanField()
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def _cidrToNetmask(self):
        bits = 0
        for i in xrange(32-self.cidr, 32):
            bits |= (1 << i)
        return "%d.%d.%d.%d" % (
            (bits & 0xff000000) >> 24,
            (bits & 0xff0000) >> 16,
            (bits & 0xff00) >> 8,
            (bits & 0xff)
        )

    netmask = property(_cidrToNetmask)

    def last_event_date(self):
        events = Event.objects.filter(attackerAddress=self.address)
        if events.count() != 0:
            event = events.reverse()[0]
            return event.created_date
        else:
            return ''
    
    def attack_score(self):
        attackscore = AttackScore.objects.filter(offender=self)
        if attackscore.count() != 0:
            attackscore.reverse()
            return attackscore[0].score

    @classmethod
    def find_create_from_ip(cls, ip):
        offender = Offender.objects.filter(address=ip)
        if offender.count() == 0:
            # IPv6
            if ':' in ip:
                # eui-64 for autoconfiguration
                if 'ff:fe' in ip or 'FF:FE' in ip:
                    cidr = 64
                else:
                    cidr = 128
            # IPv4
            else:
                cidr = 32
            
            # TODO: hostname, asn if internet access
            offender = Offender(address=ip,
                cidr=cidr,
                suggestion=True,
            )
            offender.save()
        else:
            offender = offender[0]
        return offender

class Blacklist(models.Model):
    TYPES = (('zlb_redirect', 'zlb_redirect'),
        ('zlb_block', 'zlb_block'),
        ('bgp_block', 'bgp_block'),
        ('unknown', 'unknown')
    )
    
    offender = models.ForeignKey(Offender)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    comment = models.CharField(max_length=1024)
    reporter = models.EmailField()
    bug_number = models.IntegerField(max_length=7, null=True)
    suggestion = models.BooleanField()
    type = models.CharField(max_length=12, choices=TYPES)
    
    def expired(self):
        return self.end_date <= datetime.datetime.now()

# Populated with events from ArcSight ESM
# The field names are taken from ArcSight ESM
# The attack score is the initial one (time = 0)
class Event(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    # IP address of the attacker
    attackerAddress = models.CharField(max_length=39)
    # Name of the ArcSight rule that matched
    rulename = models.CharField(max_length=255)
    # Severity of the alert (from 1 to 10, low to high)
    severity = models.IntegerField(max_length=2)
    # Event ID
    eventId = models.BigIntegerField(max_length=20)
    # Username tried by the attacker
    attackerUserName = models.CharField(max_length=255, null=True)
    # Requested URL
    requestUrl = models.TextField(null=True)
    # Host serving the requested URL?
    requestUrlHost = models.CharField(max_length=255, null=True)
    # Country of the source IP?
    sourceGeoCountryName = models.CharField(max_length=255, null=True)
    # ?
    requestContext = models.CharField(max_length=255, null=True)
    # targeted hostname?
    targetHostName = models.CharField(max_length=255, null=True)
    # ?
    targetAddress = models.CharField(max_length=39, null=True)
    # ?
    attackerGeoLocationInfo = models.CharField(max_length=255, null=True)
    # Source IP Address
    sourceAddress = models.CharField(max_length=39, null=True)
    # ?
    login = models.CharField(max_length=255, null=True)
    # ?
    referrer = models.CharField(max_length=255, null=True)
    # ?
    sourceUserName = models.CharField(max_length=255, null=True)
    # ?
    fileName = models.CharField(max_length=255, null=True)
    # ?
    getDestHostName = models.CharField(max_length=255, null=True)

class AttackScore(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    # The updated date is used to decrease the score as time passes
    updated_date = models.DateTimeField(auto_now=True)
    score = models.IntegerField(max_length=7)
    offender = models.ForeignKey(Offender)

    @classmethod
    def compute_score(cls, score_indicators, score_factors):
        score_details = {}

        for indicator in score_indicators:
            score_details[indicator] = score_indicators[indicator] * \
                score_factors[indicator]

        score_details['total'] = 0
        for i in score_details.values():
            score_details['total'] += i

        return score_details

    def compute_blacklist_suggestion(self):
        # TODO: suggest the good type
        # TODO: suggest the good duration
        unknown_threshold = int(Config.objects.get(key='blacklist_unknown_threshold').value)
        if self.score > unknown_threshold:
            return Blacklist(
                offender=self.offender,
                comment=('Suggestion by RTBH-ng (score: %i)' % self.score),
                reporter='RTBH-ng bot',
                suggestion=True,
                type='unkown'
            )

# To describe the attack score for each event
class AttackScoreHistory(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    # The updated date is used to decrease the score as time passes
    offender = models.ForeignKey(Offender)
    event = models.ForeignKey(Event)
    total_score = models.IntegerField(max_length=7)
    severity = models.IntegerField(max_length=2)
    severity_score = models.IntegerField(max_length=7)
    event_types = models.IntegerField(max_length=3)
    event_types_score = models.IntegerField(max_length=7)
    times_bgp_blocked = models.IntegerField(max_length=5)
    times_bgp_blocked_score = models.IntegerField(max_length=7)
    times_zlb_blocked = models.IntegerField(max_length=5)
    times_zlb_blocked_score = models.IntegerField(max_length=7)
    times_zlb_redirected = models.IntegerField(max_length=5)
    times_zlb_redirected_score = models.IntegerField(max_length=7)
    last_attackscore = models.IntegerField(max_length=7)
    last_attackscore_score = models.IntegerField(max_length=7)
    et_compromised_ips = models.IntegerField(max_length=1)
    et_compromised_ips_score = models.IntegerField(max_length=7)
    dshield_block = models.IntegerField(max_length=1)
    dshield_block_score = models.IntegerField(max_length=7)

    @classmethod
    def score_indicators(cls, event, offender):
        indicators = {'severity': event.severity}
        
        # previous events number
        one_day = datetime.datetime.today() - datetime.timedelta(1)
        indicators['event_types'] = Event.objects.filter(created_date__gte=one_day,
            attackerAddress=event.attackerAddress)
        indicators['event_types'] = uniquify(indicators['event_types'].values('rulename'))
        indicators['event_types'] = len(indicators['event_types'])-1
        
        # number of times bgp blocked
        indicators['times_bgp_blocked'] = Blacklist.objects.filter(
            offender=offender,
            type='bgp_block'
        ).count()
        
        # number of times zlb blocked
        indicators['times_zlb_blocked'] = Blacklist.objects.filter(
            offender=offender,
            type='zlb_block'
        ).count()
        
        # number of times redirected
        indicators['times_zlb_redirected'] = Blacklist.objects.filter(
            offender=offender.id,
            type='zlb_redirect'
        ).count()
        
        # last attack score of the offender
        indicators['last_attackscore'] = AttackScore.objects.filter(
            offender=offender)
        if len(indicators['last_attackscore']) > 0:
            indicators['last_attackscore'] = indicators['last_attackscore'][0].score
        else:
            indicators['last_attackscore'] = 0
        
        # ip in emerging threat compromised ips list?
        f = file('%s/%s' % (settings.THIRD_PARTY_RULES_FOLDER, settings.ET_COMPROMISED_IPS_CONTENT_FILE), 'r')
        indicators['et_compromised_ips'] = 0
        for l in f.readlines():
            if netaddr.IPAddress(event.attackerAddress) in netaddr.IPNetwork(l[:-1]):
                indicators['et_compromised_ips'] = 1
                break
        f.close()

        # ip in dhsield block network list?
        f = file('%s/%s' % (settings.THIRD_PARTY_RULES_FOLDER, settings.DSHIELD_BLOCK_CONTENT_FILE), 'r')
        indicators['dshield_block'] = 0
        for l in f.readlines():
            try:
                if netaddr.IPAddress(event.attackerAddress) in netaddr.IPNetwork(l[:-1]):
                    indicators['dshield_block'] = 1
                    break
            except netaddr.core.AddrFormatError:
                # comparing IPv4 and IPv6 networks
                pass
                
        f.close()

        return indicators

class WhitelistIP(models.Model):
    address = models.CharField(max_length=39)
    cidr = models.IntegerField()
    reporter = models.EmailField()
    comment = models.CharField(max_length=1024)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    @classmethod
    def is_ip_in(cls, ip):
        whitelist = WhitelistIP.objects.all()
        for n in whitelist:
            try:
                if netaddr.IPAddress(ip) in netaddr.IPNetwork("%s/%i" % (n.address, n.cidr)):
                    return True
            except netaddr.core.AddrFormatError:
                # comparing IPv4 and IPv6 networks
                pass
        return False

""" Derek Moore <dmoore@mozilla.com> 11/15/2010 """

from django.db import models
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode

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

    @classmethod
    def find_create_from_ip(cls, ip):
        offender = Offender.objects.filter(address=ip)
        if offender.count() == 0:
            # IPv6
            if ':' in options['attackerAddress']:
                # eui-64 for autoconfiguration
                if 'ff:fe' in cidr or 'FF:FE' in options['attackerAddress']:
                    cidr = 64
                else:
                    cidr = 128
            # IPv4
            else:
                cidr = 32
            
            # TODO: hostname, asn if internet access
            offender = Offender(address=event.attackerAddress,
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
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    comment = models.CharField(max_length=1024)
    reporter = models.EmailField()
    bug_number = models.IntegerField(max_length=7, null=True)
    suggestion = models.BooleanField()
    type = models.CharField(max_length=12, choices=TYPES)

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
    eventId = models.IntegerField()
    # Username tried by the attacker
    attackerUserName = models.CharField(max_length=255, null=True)
    # Requested URL
    requestUrl = models.CharField(max_length=255, null=True)
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

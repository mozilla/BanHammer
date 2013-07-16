""" Derek Moore <dmoore@mozilla.com> 11/15/2010 """

from django.db import models
from django import forms
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode

import netaddr, re

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

class Blacklist(models.Model):
    offender = models.ForeignKey(Offender)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    comment = models.CharField(max_length=1024)
    reporter = models.EmailField()
    bug_number = models.IntegerField(max_length=7, null=True)

class DisplayForm(forms.Form):

    modes = [
        ('show_expired', 'Show Expired'),
        ('hide_expired', 'Hide Expired'),
    ]

    view_mode = forms.CharField(
        widget=forms.HiddenInput(),
        initial='show_expired'
    )

class ComplaintForm(forms.Form):

    # Create a list of default blacklist durations
    durations = [
        (60 * 60,           '1 hour'),
        (60 * 60 * 12,      '12 hours'),
        (60 * 60 * 24,      '1 day'),
        (60 * 60 * 24 * 7,  '1 week'),
        (60 * 60 * 24 * 30, '30 days'),
        (0,                  'Custom...'),
    ]
    duration = forms.ChoiceField(choices=durations)

    target = forms.CharField(
        widget=forms.TextInput( attrs={'size':'43'} ),
        max_length=43
    )

    start_date = forms.DateTimeField()
    end_date = forms.DateTimeField()

    comment = forms.CharField(
        widget=forms.TextInput( attrs={'size':'50'} ),
        max_length=1024
    )

    bug_number = forms.IntegerField(
        widget=forms.TextInput( attrs={'size':'7'} ),
        required=False
    )

    # clean_target takes the target field (a v4 or v6 IP address, with
    # optional CIDR) and creates validated 'address' and 'cidr'
    # values
    def clean_target(self):
        target = self.cleaned_data['target']
        fields = target.split('/')

        try:
            address = netaddr.ip.IPAddress(fields[0])
        except netaddr.core.AddrFormatError:
            raise forms.ValidationError("Invalid IP address")

        try:
            cidr = int(fields[1])
        except ValueError:
            raise forms.ValidationError("Invalid CIDR value")
        except IndexError:
            if address.version == 4:
                cidr = 32
            else:
                cidr = 128

        if address.version == 4:
            if cidr > 32 or cidr < 16:
                raise forms.ValidationError("Invalid CIDR value")
        elif address.version == 6:
            if cidr > 128 or cidr < 32:
                raise forms.ValidationError("Invalid CIDR value")

        self.cleaned_data['address'] = fields[0]
        self.cleaned_data['cidr'] = cidr
        return target
        

    # Perform any multi-field validation after all individual fields
    # have been cleaned
    def clean(self):
        cleaned_data = self.cleaned_data
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            self._errors["end_date"] = self.error_class(["End date must come after start date"])
            del cleaned_data["end_date"]

        return cleaned_data

# Populated with events from ArcSight ESM
# The field names are taken from ArcSight ESM
# The attack score is the initial one (time = 0)
class Event(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    initial_score = models.IntegerField(max_length=7)
    # IP address of the attacker
    attackerAddress = models.CharField(max_length=39)
    # Name of the ArcSight rule that matched
    rulename = models.CharField(max_length=255)
    # Severity of the alert (from 1 to 10, low to high)
    severity = models.IntegerField(max_length=2)
    # Event ID
    eventID = models.IntegerField()
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

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from captcha.fields import CaptchaField

from models import ZLBVirtualServer, WhitelistIP

import netaddr

class BaseForm(forms.Form):
    @classmethod
    def validator_email(cls):
        return RegexValidator(
            r'^.*@.*$',
            'has to be an email address.',
            'Invalid email'
        )
    
    @classmethod
    def validator_integer(cls):
        return RegexValidator(
            r'^[0-9]+$',
            'has to be an integer.',
            'Invalid integer'
        )
        
    @classmethod
    def validator_integer_whitespace(cls):
        return RegexValidator(
            r'^([0-9]+(\s)?)+$',
            'has to be a list of integers separated by whitespaces',
            'Invalid integer list'
        )
    
    @classmethod
    def validator_whitelist_target(cls, value):
        ip = value.split('/')[0]
        if WhitelistIP.is_ip_in(ip):
            raise ValidationError(u'%s is in the IP Whitelist' % value)

class ComplaintBGPBlockForm(BaseForm):

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
        max_length=43,
        validators=[BaseForm.validator_whitelist_target],
    )

    start_date = forms.DateTimeField(required=True)
    end_date = forms.DateTimeField(required=True)

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

class ComplaintZLBForm(ComplaintBGPBlockForm):
    select = forms.ModelMultipleChoiceField(
        queryset=ZLBVirtualServer.objects.all(),
        widget=forms.CheckboxSelectMultiple)

class SettingsForm(BaseForm):
    checkbox_fields = [
        'notifications_email_new_event_enable',
        'notifications_email_delete_event_enable',
        'notifications_email_new_blacklist_enable',
        'notifications_email_delete_blacklist_enable',
        'notifications_email_new_ip_whitelist_enable',
        'notifications_email_delete_ip_whitelist_enable',
        'notifications_email_delete_offender_enable',
        'notifications_irc_new_event_enable',
        'notifications_irc_delete_event_enable',
        'notifications_irc_new_blacklist_enable',
        'notifications_irc_delete_blacklist_enable',
        'notifications_irc_new_ip_whitelist_enable',
        'notifications_irc_delete_ip_whitelist_enable',
        'notifications_irc_delete_offender_enable',]

    # Misc
    zlb_redirection_url = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
    )
    redirect_block_time = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
        validators=[BaseForm.validator_integer()],
    )
    redirect_block_url = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
    )

    # Email Notifications
    notifications_email_address_from = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
        validators=[BaseForm.validator_email()],
    )
    notifications_email_address_to = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
        validators=[BaseForm.validator_email()],
    )
    notifications_email_new_event_enable = forms.CharField(
        widget=forms.CheckboxInput(),
        max_length=255,
    )
    notifications_email_events_threshold = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
        validators=[BaseForm.validator_integer_whitespace()],
    )
    notifications_email_delete_event_enable = forms.CharField(
        widget=forms.CheckboxInput(),
        max_length=255,
    )
    notifications_email_new_blacklist_enable = forms.CharField(
        widget=forms.CheckboxInput(),
        max_length=255,
    )
    notifications_email_delete_blacklist_enable = forms.CharField(
        widget=forms.CheckboxInput(),
        max_length=255,
    )
    notifications_email_new_ip_whitelist_enable = forms.CharField(
        widget=forms.CheckboxInput(),
        max_length=255,
    )
    notifications_email_delete_ip_whitelist_enable = forms.CharField(
        widget=forms.CheckboxInput(),
        max_length=255,
    )
    notifications_email_delete_offender_enable = forms.CharField(
        widget=forms.CheckboxInput(),
        max_length=255,
    )

    # IRC notifications
    notifications_irc_new_event_enable = forms.CharField(
        widget=forms.CheckboxInput(),
        max_length=255,
    )
    notifications_irc_events_threshold = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
        validators=[BaseForm.validator_integer_whitespace()],
    )
    notifications_irc_delete_event_enable = forms.CharField(
        widget=forms.CheckboxInput(),
        max_length=255,
    )
    notifications_irc_new_blacklist_enable = forms.CharField(
        widget=forms.CheckboxInput(),
        max_length=255,
    )
    notifications_irc_delete_blacklist_enable = forms.CharField(
        widget=forms.CheckboxInput(),
        max_length=255,
    )
    notifications_irc_new_ip_whitelist_enable = forms.CharField(
        widget=forms.CheckboxInput(),
        max_length=255,
    )
    notifications_irc_delete_ip_whitelist_enable = forms.CharField(
        widget=forms.CheckboxInput(),
        max_length=255,
    )
    notifications_irc_delete_offender_enable = forms.CharField(
        widget=forms.CheckboxInput(),
        max_length=255,
    )

    # Score
    score_factor_severity = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
        validators=[BaseForm.validator_integer()],
    )
    score_factor_event_types = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
        validators=[BaseForm.validator_integer()],
    )
    score_factor_times_bgp_blocked = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
        validators=[BaseForm.validator_integer()],
    )
    score_factor_times_zlb_blocked = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
        validators=[BaseForm.validator_integer()],
    )
    score_factor_times_zlb_redirected = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
        validators=[BaseForm.validator_integer()],
    )
    score_factor_last_attackscore = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
        validators=[BaseForm.validator_integer()],
    )
    score_factor_et_compromised_ips = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
        validators=[BaseForm.validator_integer()],
    )
    score_factor_dshield_block = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
        validators=[BaseForm.validator_integer()],
    )
    score_decrease = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
        validators=[BaseForm.validator_integer()],
    )

    def clean(self):
        cleaned_data = self.cleaned_data
        for i in self.checkbox_fields:
            if cleaned_data[i] == 'on':
                cleaned_data[i] = '1'
            else:
                cleaned_data[i] = '0'
        
        return cleaned_data

class WhitelistIPForm(BaseForm):
    target = forms.CharField(
        widget=forms.TextInput( attrs={'size':'43'} ),
        max_length=43
    )

    comment = forms.CharField(
        widget=forms.TextInput( attrs={'size':'50'} ),
        max_length=1024
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

        self.cleaned_data['address'] = address
        self.cleaned_data['cidr'] = cidr
        return target

class OffenderForm(BaseForm):
    hostname = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
        required=False,
    )
    
    asn = forms.CharField(
        widget=forms.TextInput(),
        max_length=8,
        required=False,
        validators=[BaseForm.validator_integer()],
    )
    
    score = forms.CharField(
        widget=forms.TextInput(),
        max_length=7,
        required=False,
        validators=[BaseForm.validator_integer()],
    )
    
    def clean_asn(self):
        if self.cleaned_data['asn']:
            return int(self.cleaned_data['asn'])
        return None
    
    def clean_score(self):
        if self.cleaned_data['score']:
            return int(self.cleaned_data['score'])
        return None

class ZLBForm(BaseForm):
    name = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
    )
    
    hostname = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
    )
    
    datacenter = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
        required=False,
    )
    
    comment = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
        required=False,
    )
    
    doc_url = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
        required=False,
    )

    login = forms.CharField(
        widget=forms.TextInput(),
        max_length=255,
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(),
        max_length=255,
        required=False,
    )

class PortalForm(BaseForm):
    captcha = CaptchaField()
    referer = forms.CharField(
        widget=forms.HiddenInput(),
        max_length=255,
    )

class VirtualServerConfirm(BaseForm):
    confirm = forms.CharField(
        widget=forms.Textarea(),
    )

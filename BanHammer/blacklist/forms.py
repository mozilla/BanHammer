from django import forms

import netaddr

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

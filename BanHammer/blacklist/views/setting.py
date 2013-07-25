from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist

from django.http import HttpResponse, HttpResponseRedirect
from session_csrf import anonymous_csrf
from ..models import Config
from ..forms import SettingsForm

import logging


@anonymous_csrf
def list(request):
    if request.method == 'POST':
        form = SettingsForm(request.POST)
        if form.is_valid():
            for field in form:
                config = Config.objects.get(key=field.__dict__['html_name'])
                config.value = form.cleaned_data[field.__dict__['html_name']]
                config.save()
        else:
            logging.error(form.errors)
    else:
        initial = {}
        data = {}
        for i in Config.objects.all():
            initial[i.key] = i.value

        for i in SettingsForm.checkbox_fields:
            initial[i] = (initial[i] == '1')
        
        form = SettingsForm(initial)
    
    return render_to_response(
        'setting/index.html',
        {'form': form },
        context_instance = RequestContext(request)
    )

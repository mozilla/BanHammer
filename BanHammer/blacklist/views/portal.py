from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist

from django.http import HttpResponse, HttpResponseRedirect
from session_csrf import anonymous_csrf

from BanHammer.blacklist.forms import PortalForm
from BanHammer.blacklist import models
from BanHammer import settings

import logging
from urlparse import urlparse
import netaddr
import hashlib

@anonymous_csrf
def index(request):
    if request.POST:
        form = PortalForm(request.POST)
        if form.is_valid():
            referer = form.cleaned_data['referer']
            parse = urlparse(referer)
            for b in models.Blacklist.objects.filter(removed=False, type='zlb_redirect'):
                if not b.expired():
                    ip = request.META.get('REMOTE_ADDR')
                    n = b.offender
                    if netaddr.IPAddress(ip) in netaddr.IPNetwork("%s/%i" % (n.address, n.cidr)):
                        black_id = str(b.id)
                        secret = hashlib.sha256(settings.SALT+black_id).hexdigest()
            logging.debug('black_id: %s' % black_id)
            logging.debug('secret: %s' % secret)
            if parse.query:
                return HttpResponseRedirect(referer+'&'+secret)
            else:
                return HttpResponseRedirect(referer+'?'+secret)
    else:
        url = request.GET.get('url')
        form = PortalForm(initial={'referer': url})
    return render_to_response(
        'portal/index.html',
        {'form': form,},
        context_instance = RequestContext(request)
    )

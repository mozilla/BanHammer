from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from session_csrf import anonymous_csrf

from ..models import Offender, Event, Blacklist, AttackScore
from ..forms import OffenderForm

import logging

def index(request, show_suggested=False):
    request.session['order_by'] = request.GET.get('order_by', request.session.get('order_by', 'address'))
    request.session['order'] = request.GET.get('order', request.session.get('order', 'asc'))

    order_by = request.session.get('order_by', 'address')
    order = request.session.get('order', 'asc')

    if show_suggested:
        offenders = Offender.objects.filter()
    else:
        offenders = Offender.objects.filter(suggestion=False)

    if order_by == 'address':
        offenders = sorted(list(offenders), key=lambda offender: offender.address)
    elif order_by == 'cidr':
        offenders = sorted(list(offenders), key=lambda offender: offender.cidr)
    elif order_by == 'created_date':
        offenders = sorted(list(offenders), key=lambda offender: offender.created_date)
    elif order_by == 'attackscore':
        offenders = sorted(list(offenders), key=lambda offender: offender.attack_score())

    if order == 'desc':
        offenders.reverse()

    data = {
        'show_suggested': show_suggested,
    }

    return render_to_response(
        'offender/index.html',
        {'offenders': offenders, 'data': data},
        context_instance = RequestContext(request)
    )

@anonymous_csrf
def show(request, id):
    offender = Offender.objects.get(id=id)
    blacklists = Blacklist.objects.filter(offender=offender,suggestion=False)
    attackscore = None
    events = Event.objects.filter(attackerAddress=offender.address)
    
    return render_to_response(
        'offender/show.html',
        {'offender': offender,
         'blacklists': blacklists,
         'events': events,
         'attackscore': attackscore},
        context_instance = RequestContext(request)
    )

@anonymous_csrf
def delete(request, id):
    offender = Offender.objects.get(id=id)
    offender.delete()
    
    return HttpResponseRedirect('/offenders')

@anonymous_csrf
def edit(request, id):
    if request.method == 'POST':
        form = OffenderForm(request.POST)
        if form.is_valid():
            address = form.cleaned_data['address']
            cidr = form.cleaned_data['cidr']
            hostname = form.cleaned_data['hostname']
            asn = form.cleaned_data['asn']

            offender = Offender.objects.get(id=id)
            offender.address = address.split('/')[0]
            offender.cidr = cidr
            offender.hostname = hostname
            offender.asn = asn
            offender.save()
            
            return HttpResponseRedirect('/offender/%s' % id)
    else:
        initial = Offender.objects.get(id=id)
        initial = initial.__dict__
        initial['address'] += '/'+str(initial['cidr'])
        id = initial['id']
        form = OffenderForm(initial)
        
    return render_to_response(
        'offender/edit.html',
        {'form': form, 'id': id},
        context_instance = RequestContext(request)
    )

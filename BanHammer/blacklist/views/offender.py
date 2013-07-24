from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist

from django.http import HttpResponse, HttpResponseRedirect
from session_csrf import anonymous_csrf
from ..models import Offender
from ..forms import SuggestedOffendersSwitch

@anonymous_csrf
def list(request):
    if request.method == 'POST':
        form = SuggestedOffendersSwitch(request.POST)
        if form.is_valid():
           if form.cleaned_data['view_mode'] == 'show_suggested':
                request.session['show_suggested'] = 1
           elif form.cleaned_data['view_mode'] == 'hide_suggested':
                request.session['show_suggested'] = 0
    else:
        form = SuggestedOffendersSwitch()
    
    show_suggested = request.session.get('show_suggested', 0)
    order_by = request.session.get('order_by', 'last_event_date')
    order = request.session.get('order', 'asc')

    if show_suggested:
        offenders = Offender.objects.filter()
    else:
        offenders = Offender.objects.filter(suggestion=False)

    if order_by == 'address':
        offenders = sorted(list(offenders), key=lambda offender: offender.address)
    elif order_by == 'cidr':
        offenders = sorted(list(blacklists), key=lambda offender: offender.cidr)
    elif order_by == 'created_date':
        offenders = sorted(list(blacklists), key=lambda offender: offender.cidr)
    elif order_by == 'last_event':
        offenders = sorted(list(blacklists), key=lambda offender: offender.cidr)

    if order == 'desc':
        offenders.reverse()

    data = {
        'show_suggested': show_suggested,
    }

    return render_to_response(
        'offender/index.html',
        {'offenders': offenders, 'form': form, 'data': data },
        context_instance = RequestContext(request)
    )

@anonymous_csrf
def show(request):
    pass

@anonymous_csrf
def create(request):
    pass

@anonymous_csrf
def edit(request):
    pass

@anonymous_csrf
def delete(request):
    pass
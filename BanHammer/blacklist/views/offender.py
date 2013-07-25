from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist

from django.http import HttpResponse, HttpResponseRedirect
from session_csrf import anonymous_csrf
from ..models import Offender

@anonymous_csrf
def list(request, show_suggested=False):
    request.session['order_by'] = request.GET.get('order_by', request.session.get('order_by', 'end_date'))
    request.session['order'] = request.GET.get('order', request.session.get('order', 'asc'))

    order_by = request.session.get('order_by', 'last_event_date')
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
    elif order_by == 'last_event_date':
        offenders = sorted(list(offenders), key=lambda offender: offender.get_last_event_date())
    elif order_by == 'attackscore':
        offenders = sorted(list(offenders), key=lambda offender: offender.get_attack_score())

    if order == 'desc':
        offenders.reverse()

    data = {
        'show_suggested': show_suggested,
    }

    return render_to_response(
        'offender/index.html',
        {'offenders': offenders, 'data': data },
        context_instance = RequestContext(request)
    )

@anonymous_csrf
def show(request):
    pass

@anonymous_csrf
def edit(request):
    pass

@anonymous_csrf
def delete(request, id):
    offender = Offender.objects.get(id=id)
    offender.delete()
    
    return HttpResponseRedirect('/offenders')

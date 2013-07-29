""" Derek Moore <dmoore@mozilla.com> 11/15/2010 """

from django.shortcuts import render_to_response
from django.template import RequestContext
from datetime import datetime, timedelta
from django.core.exceptions import ObjectDoesNotExist

from django.http import HttpResponse, HttpResponseRedirect
from session_csrf import anonymous_csrf
from ..models import Offender, Blacklist
from ..forms import ComplaintBGPBlockForm


# default view for displaying all blacklists
@anonymous_csrf
def index(request, show_expired=False):
    request.session['order_by'] = request.GET.get('order_by', request.session.get('order_by', 'end_date'))
    request.session['order'] = request.GET.get('order', request.session.get('order', 'asc'))

    order_by = request.session.get('order_by', 'end_date')
    order = request.session.get('order', 'asc')

    if show_expired:
        blacklists = Blacklist.objects.filter(suggestion=False)
    else:
        blacklists = Blacklist.objects.filter(end_date__gt=datetime.now(),suggestion=False)

    if order_by == 'address':
        blacklists = sorted(list(blacklists), key=lambda blacklist: blacklist.offender.address)
    elif order_by == 'cidr':
        blacklists = sorted(list(blacklists), key=lambda blacklist: blacklist.offender.cidr)
    elif order_by == 'type':
        blacklists = sorted(list(blacklists), key=lambda blacklist: blacklist.type)
    elif order_by == 'start_date':
        blacklists = sorted(list(blacklists), key=lambda blacklist: blacklist.start_date)
    elif order_by == 'end_date':
        blacklists = sorted(list(blacklists), key=lambda blacklist: blacklist.end_date)
    elif order_by == 'reporter':
        blacklists = sorted(list(blacklists), key=lambda blacklist: blacklist.reporter)

    if order == 'desc':
        blacklists.reverse()

    data = {
        'show_expired': show_expired,
    }

    return render_to_response(
        'blacklist/index.html',
        {'blacklists': blacklists, 'data': data },
        context_instance = RequestContext(request)
    )

# view for creating new blacklists
@anonymous_csrf
def new_bgp_block(request, id=None):
    if request.method == 'POST':
        form = ComplaintBGPBlockForm(request.POST)
        if form.is_valid():

            address = form.cleaned_data['address']
            cidr = form.cleaned_data['cidr']
            type = "bgp_block"
            comment = form.cleaned_data['comment']
            bug_number = form.cleaned_data['bug_number']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            #reporter = 'test' #//XXX
            reporter = request.META.get("REMOTE_USER")

            # Fetch/create the Offender and Blacklist objects.
            o, new = Offender.objects.get_or_create(
                address=address,
                cidr=cidr
            )
            o.save()

            b = Blacklist(
                type=type,
                start_date=start_date,
                end_date=end_date,
                comment=comment,
                bug_number=bug_number,
                reporter=reporter,
                offender=o
            )
            b.save()

            return HttpResponseRedirect('/blacklist')

    else:
        if id:
            offender = Offender.objects.get(id=id)
            initial = {}
            initial['target'] = '%s/%s' % (offender.address, offender.cidr)
            form = ComplaintBGPBlockForm(initial=initial)
        else:
            form = ComplaintBGPBlockForm()

    return render_to_response(
        'blacklist/new_bgp_block.html',
        {'form': form,
         'body_init': True},
        context_instance = RequestContext(request)
    )


# view for deleting blacklists
@anonymous_csrf
def delete(request):
    if request.method == 'GET':

        # Insert a confirmation dialog, at some point

        id = request.GET.get('id')

	if not id.isdigit():
            return HttpResponseRedirect('/blacklist')
		
        try:
            b = Blacklist.objects.get(id=id)
            b.delete()
        except ObjectDoesNotExist:
            return HttpResponseRedirect('/blacklist')

    return HttpResponseRedirect('/blacklist')

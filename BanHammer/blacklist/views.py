""" Derek Moore <dmoore@mozilla.com> 11/15/2010 """

from django.shortcuts import render_to_response
from django.template import RequestContext
from datetime import datetime, timedelta
from django.core.exceptions import ObjectDoesNotExist

from django.http import HttpResponse, HttpResponseRedirect
from session_csrf import anonymous_csrf
from .models import Offender, Blacklist
from .forms import ComplaintForm, DisplayForm


# default view for displaying all blacklists
@anonymous_csrf
def index(request):

    if request.method == 'POST':
        form = DisplayForm(request.POST)
        if form.is_valid():
           if form.cleaned_data['view_mode'] == 'show_expired':
                request.session['show_expired'] = 1
           elif form.cleaned_data['view_mode'] == 'hide_expired':
                request.session['show_expired'] = 0

    else:
        request.session['order_by'] = request.GET.get('order_by', request.session.get('order_by', 'end_date'))
        request.session['order'] = request.GET.get('order', request.session.get('order', 'asc'))
        form = DisplayForm()


    show_expired = request.session.get('show_expired', 0)
    order_by = request.session.get('order_by', 'end_date')
    order = request.session.get('order', 'asc')

    if show_expired:
        blacklists = Blacklist.objects.all()
    else:
        blacklists = Blacklist.objects.filter(end_date__gt=datetime.now())

    if order_by == 'address':
        blacklists = sorted(list(blacklists), key=lambda blacklist: blacklist.offender.address)
    elif order_by == 'cidr':
        blacklists = sorted(list(blacklists), key=lambda blacklist: blacklist.offender.cidr)
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
        {'blacklists': blacklists, 'form': form, 'data': data },
        context_instance = RequestContext(request)
    )

# view for creating new blacklists
@anonymous_csrf
def post(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():

            address = form.cleaned_data['address']
            cidr = form.cleaned_data['cidr']
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
        form = ComplaintForm()

    return render_to_response(
        'blacklist/post.html',
        {'form': form},
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

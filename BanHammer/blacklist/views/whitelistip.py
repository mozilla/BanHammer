from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist

from django.http import HttpResponse, HttpResponseRedirect
from session_csrf import anonymous_csrf
from ..models import WhitelistIP
from ..forms import WhitelistIPForm
from BanHammer.blacklist import tasks

@anonymous_csrf
def index(request, show_suggested=False):
    request.session['order_by'] = request.GET.get('order_by', 'created_date')
    request.session['order'] = request.GET.get('order', 'desc')

    order_by = request.session.get('order_by', 'address')
    order = request.session.get('order', 'asc')

    whitelistip = WhitelistIP.objects.all()

    if order_by == 'address':
        whitelistip = sorted(list(whitelistip), key=lambda ip: ip.address)
    elif order_by == 'cidr':
        whitelistip = sorted(list(whitelistip), key=lambda ip: ip.cidr)
    elif order_by == 'reporter':
        whitelistip = sorted(list(whitelistip), key=lambda ip: ip.cidr)
    elif order_by == 'created_date':
        whitelistip = sorted(list(whitelistip), key=lambda ip: ip.created_date)
    elif order_by == 'updated_date':
        whitelistip = sorted(list(whitelistip), key=lambda ip: ip.updated_date)

    if order == 'desc':
        whitelistip.reverse()

    return render_to_response(
        'whitelistip/index.html',
        {'whitelistip': whitelistip},
        context_instance = RequestContext(request)
    )

@anonymous_csrf
def delete(request, id):
    reporter = request.META.get("REMOTE_USER")
    if not reporter:
        reporter = 'test'
    whitelistip = WhitelistIP.objects.get(id=id)
    tasks.notification_delete_ip_whitelist.delay(whitelistip.__dict__, reporter)
    whitelistip.delete()
    
    return HttpResponseRedirect('/whitelistip')

@anonymous_csrf
def new(request):
    if request.method == 'POST':
        form = WhitelistIPForm(request.POST)
        if form.is_valid():
            address = form.cleaned_data['address']
            cidr = form.cleaned_data['cidr']
            comment = form.cleaned_data['comment']
            reporter = request.META.get("REMOTE_USER")
            if not reporter:
                reporter = 'test'

            whitelist = WhitelistIP(
                address=address,
                cidr=cidr,
                comment=comment,
                reporter=reporter,
            )
            whitelist.save()
            tasks.notification_add_ip_whitelist.delay(whitelist.__dict__)
            
            return HttpResponseRedirect('/whitelistip')
    else:
        form = WhitelistIPForm()
        
    return render_to_response(
        'whitelistip/new.html',
        {'form': form},
        context_instance = RequestContext(request)
    )

@anonymous_csrf
def edit(request, id):
    if request.method == 'POST':
        form = WhitelistIPForm(request.POST)
        if form.is_valid():
            address = form.cleaned_data['address']
            cidr = form.cleaned_data['cidr']
            comment = form.cleaned_data['comment']
            reporter = request.META.get("REMOTE_USER")
            if not reporter:
                reporter = 'test'

            whitelist = WhitelistIP.objects.get(id=id)
            whitelist.address = address
            whitelist.cidr = cidr
            whitelist.comment = comment
            whitelist.reporter = reporter
            whitelist.save()
            
            return HttpResponseRedirect('/whitelistip')
    else:
        initial = WhitelistIP.objects.get(id=id)
        initial = initial.__dict__
        initial['target'] = initial['address']+'/'+str(initial['cidr'])
        id = initial['id']
        form = WhitelistIPForm(initial)
        
    return render_to_response(
        'whitelistip/edit.html',
        {'form': form, 'id': id},
        context_instance = RequestContext(request)
    )

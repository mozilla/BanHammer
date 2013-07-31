from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.cache import never_cache
from django.http import HttpResponse, HttpResponseRedirect
from session_csrf import anonymous_csrf

from ..models import ZLB, ZLBVirtualServer, ZLBVirtualServerRule, ZLBVirtualServerProtection
from ..models import ZLBRule, ZLBProtection, Offender
from ..forms import ZLBForm
from BanHammer.blacklist.management import zeus
import BanHammer.blacklist.tasks as tasks

@anonymous_csrf
@never_cache
def index(request, zlb=None, action=None):
    request.session['order_by'] = request.GET.get('order_by', 'hostname')
    request.session['order'] = request.GET.get('order', 'asc')

    order_by = request.session.get('order_by', 'address')
    order = request.session.get('order', 'asc')

    zlbs = ZLB.objects.all()

    if order_by == 'created_date':
        zlbs = sorted(list(zlbs), key=lambda zlb: zlb.created_date)
    elif order_by == 'updated_date':
        zlbs = sorted(list(zlbs), key=lambda zlb: zlb.updated_date)
    elif order_by == 'name':
        zlbs = sorted(list(zlbs), key=lambda zlb: zlb.name)
    elif order_by == 'hostname':
        zlbs = sorted(list(zlbs), key=lambda zlb: zlb.hostname)
    elif order_by == 'datacenter':
        zlbs = sorted(list(zlbs), key=lambda zlb: zlb.datacenter)

    if order == 'desc':
        zlbs.reverse()

    data = {'zlbs': zlbs}
    
    if action == 'update':
        data['zlb'] = zlb
        data['action'] = 'update'

    return render_to_response(
        'zlb/index.html',
        data,
        context_instance = RequestContext(request)
    )

@anonymous_csrf
def new(request):
    if request.method == 'POST':
        form = ZLBForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            hostname = form.cleaned_data['hostname']
            datacenter = form.cleaned_data['datacenter']
            doc_url = form.cleaned_data['doc_url']
            login = form.cleaned_data['login']
            password = form.cleaned_data['password']
            comment = form.cleaned_data['comment']

            zlb = ZLB(
                name=name,
                hostname=hostname,
                datacenter=datacenter,
                doc_url=doc_url,
                login=login,
                password=password,
                comment=comment,
            )
            zlb.save()
            
            return HttpResponseRedirect('/zlbs')
    else:
        form = ZLBForm()
        
    return render_to_response(
        'zlb/new.html',
        {'form': form},
        context_instance = RequestContext(request)
    )

@anonymous_csrf
def edit(request, id):
    if request.method == 'POST':
        form = ZLBForm(request.POST)
        if form.is_valid():
            zlb = ZLB.objects.get(id=id)
            zlb.name = form.cleaned_data['name']
            zlb.hostname = form.cleaned_data['hostname']
            zlb.datacenter = form.cleaned_data['datacenter']
            zlb.doc_url = form.cleaned_data['doc_url']
            zlb.comment = form.cleaned_data['comment']
            zlb.login = form.cleaned_data['login']
            if form.cleaned_data['password']:
                zlb.password = form.cleaned_data['password']
            zlb.save()
            
            return HttpResponseRedirect('/zlbs')
    else:
        initial = ZLB.objects.get(id=id)
        initial = initial.__dict__
        id = initial['id']
        initial['password'] = ''
        form = ZLBForm(initial)
        
    return render_to_response(
        'zlb/edit.html',
        {'form': form, 'id': id},
        context_instance = RequestContext(request)
    )

@anonymous_csrf
def delete(request, id):
    zlb = ZLB.objects.get(id=id)
    zlb.delete()
    
    return HttpResponseRedirect('/zlbs')

@anonymous_csrf
@never_cache
def show(request, id):
    zlb = ZLB.objects.get(id=id)
    if zlb.updating:
        return render_to_response(
            'zlb/updating.html',
            {'zlb': zlb,},
            context_instance = RequestContext(request)
        )
        
    vs = ZLBVirtualServer.objects.filter(zlb_id=zlb.id)
    pr = {}
    rul = {}
    return render_to_response(
        'zlb/show.html',
        {'zlb': zlb,
         'vs': vs,},
        context_instance = RequestContext(request)
    )

@anonymous_csrf
@never_cache
def update(request, id):
    tasks.update_zlb.delay(id)
    zlb = ZLB.objects.get(id=id)
    return HttpResponseRedirect('/zlbs')

@anonymous_csrf
def index_protection(request, zlb_id):
    def _parse_addr(addresses):
        addr_list = addresses.split(', ')
        addresses = []
        for addr in addr_list:
            network = addr.split('/')
            addr = network[0]
            if len(network) == 2:
                cidr = network[1]
            else:
                cidr = None
            if cidr:
                offender = Offender.objects.filter(address=addr, cidr=cidr)
            else:
                offender = Offender.objects.filter(address=addr)
            if offender.count() != 0:
                addresses.append(offender[0])
            else:
                addresses.append(addr)
        return addresses
    
    zlb = ZLB.objects.get(id=zlb_id)
    protections = ZLBProtection.objects.filter(zlb_id=zlb_id)
    for p in protections:
        p.allowed_addresses = _parse_addr(p.allowed_addresses)
        p.banned_addresses = _parse_addr(p.banned_addresses)
        p.virtual_servers = ZLBVirtualServerProtection.objects.filter(zlb_id=zlb_id, protection_id=p.id)
        
    return render_to_response(
        'zlb/protections.html',
        {'zlb': zlb,
         'protections': protections,},
        context_instance = RequestContext(request)
    )

@anonymous_csrf
def index_rules(request, zlb_id):
    offender_t = Offender
    zlb = ZLB.objects.get(id=zlb_id)
    rules = ZLBRule.objects.filter(zlb_id=zlb_id)
    for rule in rules:
        rule.virtual_servers = ZLBVirtualServerRule.objects.filter(zlb_id=zlb_id, rule_id=rule.id)
    
    return render_to_response(
        'zlb/rules.html',
        {'zlb': zlb,
         'rules': rules,},
        context_instance = RequestContext(request)
    )

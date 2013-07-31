from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.cache import never_cache
from django.http import HttpResponse, HttpResponseRedirect
from session_csrf import anonymous_csrf

from ..models import ZLB, ZLBVirtualServer, ZLBVirtualServerRule, ZLBVirtualServerProtection
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
def show_old(request, id):
    zlb = ZLB.objects.get(id=id)
    z = zeus.ZLB(zlb.hostname, zlb.login, zlb.password)
    z.connect('VirtualServer')

    vs = {}
    names = list(z.conn.getVirtualServerNames())
    for i in names:
        vs[i] = {}
        enabled = z.conn.getEnabled([i])[0]
        vs[i]['enabled'] = enabled
        basicInfo = z.conn.getBasicInfo([i])[0]
        vs[i]['port'] = basicInfo.port
        vs[i]['protocol'] = basicInfo.protocol
        vs[i]['default_pool'] = basicInfo.default_pool

    return render_to_response(
        'zlb/show.html',
        {'vs': vs,
         'zlb': zlb,},
        context_instance = RequestContext(request)
    )

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

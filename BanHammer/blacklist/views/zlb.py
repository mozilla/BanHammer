from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist

from django.http import HttpResponse, HttpResponseRedirect
from session_csrf import anonymous_csrf
from ..models import ZLB
from ..forms import ZLBForm

@anonymous_csrf
def index(request):
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

    return render_to_response(
        'zlb/index.html',
        {'zlbs': zlbs},
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

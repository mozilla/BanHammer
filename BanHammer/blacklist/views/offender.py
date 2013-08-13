from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from session_csrf import anonymous_csrf
from django.core.paginator import Paginator

from ..models import Offender, Event, Blacklist, AttackScoreHistory, ZLBBlacklist
from ..forms import OffenderForm
from BanHammer.blacklist import tasks

def index(request, show_suggested=False):
    if show_suggested:
        offenders = Offender.objects.filter()
    else:
        offenders = Offender.objects.filter(suggestion=False)

    data = {
        'show_suggested': show_suggested,
    }

    return render_to_response(
        'offender/index.html',
        {'offenders': offenders, 'data': data},
        context_instance = RequestContext(request)
    )

@anonymous_csrf
def show_ip(request, ip):
    offender = Offender.objects.filter(address=ip)
    if offender.count() != 1:
        return HttpResponseRedirect('/offenders')
    else:
        return show(request, offender[0].id)

@anonymous_csrf
def show(request, id):
    offender = Offender.objects.get(id=id)
    blacklists = Blacklist.objects.filter(offender=offender,suggestion=False)
    events = Event.objects.filter(attackerAddress=offender.address)
    
    for e in events:
        e.attackscore = AttackScoreHistory.objects.filter(event=e)
        if e.attackscore.count() != 0:
            e.attackscore = e.attackscore[0]
        else:
            e.attackscore = None
    
    zlb_blacklists_o = ZLBBlacklist.objects.all()
    zlb_blacklist = {}
    for z in zlb_blacklists_o:
        if z.blacklist_id not in zlb_blacklist.keys():
            zlb_blacklist[z.blacklist_id] = [z]
        else:
            zlb_blacklist[z.blacklist_id].append(z)
    for b in blacklists:
        if b.type in ['zlb_redirect', 'zlb_block']:
            b.virtual_servers = zlb_blacklist[b.id]
    
    return render_to_response(
        'offender/show.html',
        {'offender': offender,
         'blacklists': blacklists,
         'events': events,},
        context_instance = RequestContext(request)
    )

@anonymous_csrf
def delete(request, id):
    offender = Offender.objects.get(id=id)
    protections_vs = []
    protections = Blacklist.objects.filter(offender=offender,type="zlb_block")
    for p in protections:
        vs = ZLBBlacklist.objects.filter(blacklist=p)
        for v in vs:
            protections_vs.append((v.zlb_id, v.virtual_server_name))
    redirections_vs = []
    redirections = Blacklist.objects.filter(offender=offender,type="zlb_redirect")
    for p in redirections:
        vs = ZLBBlacklist.objects.filter(blacklist=p)
        for v in vs:
            redirections_vs.append((v.zlb_id, v.virtual_server_name))
    
    reporter = request.META.get("REMOTE_USER")
    if not reporter:
        reporter = 'test'
    tasks.notification_delete_offender.delay(offender.__dict__, reporter)
    tasks.delete_offender.delay(offender.address, offender.cidr, protections_vs, redirections_vs)
    events_o = Event.objects.filter(attackerAddress=offender.address)
    for event in events_o:
        event.delete()
    offender.delete()
    
    return HttpResponseRedirect('/offenders')

@anonymous_csrf
def edit(request, id):
    if request.method == 'POST':
        form = OffenderForm(request.POST)
        if form.is_valid():
            hostname = form.cleaned_data['hostname']
            asn = form.cleaned_data['asn']
            score = form.cleaned_data['score']
            
            offender = Offender.objects.get(id=id)
            offender.hostname = hostname
            offender.asn = asn
            offender.score = score
            offender.save()
            
            return HttpResponseRedirect('/offender/%s' % id)
    else:
        offender = Offender.objects.get(id=id)
        initial = offender.__dict__
        id = initial['id']
        form = OffenderForm(initial)
        
    return render_to_response(
        'offender/edit.html',
        {'form': form, 'id': id, 'offender': offender},
        context_instance = RequestContext(request)
    )

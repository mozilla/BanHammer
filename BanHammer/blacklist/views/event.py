# delete
# delete and recompute the score

from django.shortcuts import render_to_response
from django.template import RequestContext

from django.http import HttpResponse, HttpResponseRedirect
from session_csrf import anonymous_csrf
from ..models import Event, Offender, AttackScoreHistory
from BanHammer.blacklist import tasks

@anonymous_csrf
def delete(request, id):
    event = Event.objects.get(id=id)
    offender = Offender.objects.get(address=event.attackerAddress)
    attackscore = AttackScoreHistory.objects.get(event=event)
    
    reporter = request.META.get("REMOTE_USER")
    if not reporter:
        reporter = 'test'
    tasks.notification_delete_event.delay(event.__dict__, reporter)
    
    # Substracting the attack score of the event from the offender score
    offender.score -= attackscore.total_score
    offender.save()
    
    event.delete()
    
    return HttpResponseRedirect('/offender/%s' % offender.id)

from BanHammer.blacklist.models import Blacklist, Offender, AttackScore, Event, AttackScoreHistory

def given_offender_blocked():
    offender = Offender(
        address='8.8.8.8',
        cidr=32,
        suggestion=False,
        created_date = '2013-01-01 01:00:00',
        updated_date = '2013-01-01 02:00:00',
    )
    offender.save()
    
    blacklist = Blacklist(
        offender=offender,
        start_date='2013-01-01 01:01',
        end_date='2013-01-01 13:01',
        comment='testlist',
        reporter='test@example.com',
        bug_number=12345,
        suggestion=False,
        type='bgp_block',
    )
    blacklist.save()

def given_offender_suggested():
    event = Event(
        created_date = '2013-01-01 01:00:00',
        attackerAddress='4.2.2.1',
        rulename='Test Rule',
        severity=2,
        eventId=876781,
        attackerUserName='Script Kiddie',
    )
    event.save()
    
    offender = Offender(
        address='4.2.2.1',
        cidr=32,
        suggestion=True,
        created_date = '2013-01-01 01:00:00',
        updated_date = '2013-01-01 02:00:00',
    )
    offender.save()
    
    attackscore = AttackScore(
        created_date = '2013-01-01 01:00:00',
        updated_date = '2013-01-01 02:00:00',
        score=30,
        offender=offender,
    )
    attackscore.save()
    
    attackscorehistory = AttackScoreHistory(
        created_date = '2013-01-01 01:00:00',
        offender=offender,
        event=event,
        total_score=30,
        severity=2,
        severity_score=2,
        event_types=4,
        event_types_score=8,
        times_bgp_blocked=0,
        times_bgp_blocked_score=0,
        times_zlb_blocked=0,
        times_zlb_blocked_score=0,
        times_zlb_redirected=0,
        times_zlb_redirected_score=0,
        last_attackscore=0,
        last_attackscore_score=0,
        et_compromised_ips=1,
        et_compromised_ips_score=20,
        dshield_block=0,
        dshield_block_score=0,
    )
    attackscorehistory.save()
    
    blacklist = Blacklist(
        offender=offender,
        start_date='2013-01-01 01:01',
        end_date='2013-01-01 13:01',
        comment='testlist',
        reporter='test@example.com',
        bug_number=12345,
        suggestion=True,
        type='unknown',
    )

def given_another_event():
    event = Event(
        created_date = '2013-01-01 01:00:00',
        attackerAddress='4.2.2.1',
        rulename='Test Rule',
        severity=2,
        eventId=876782,
        attackerUserName='Another Script Kiddie',
    )
    event.save()
    
    offender = Offender.objects.get(address='4.2.2.1', cidr=32)
    
    attackscore = AttackScore.objects.get(offender=offender)
    attackscore.score = 60
    attackscore.save()
    
    attackscorehistory = AttackScoreHistory(
        created_date = '2013-01-01 01:00:00',
        offender=offender,
        event=event,
        total_score=30,
        severity=2,
        severity_score=2,
        event_types=4,
        event_types_score=8,
        times_bgp_blocked=0,
        times_bgp_blocked_score=0,
        times_zlb_blocked=0,
        times_zlb_blocked_score=0,
        times_zlb_redirected=0,
        times_zlb_redirected_score=0,
        last_attackscore=0,
        last_attackscore_score=0,
        et_compromised_ips=1,
        et_compromised_ips_score=20,
        dshield_block=0,
        dshield_block_score=0,
    )
    attackscorehistory.save()

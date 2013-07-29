from BanHammer.blacklist import models

from django.test import TestCase
import nose.tools as nt

def test_uniquify():
    input = [{'rulename': ''},
             {'rulename': 'test1'},
             {'rulename': ''},
             {'rulename': 'test2'},
             {'rulename': 'test2'}]
    nt.assert_equal(models.uniquify(input), ['', 'test1', 'test2'])

class TestOffender(object):

    def setup(self):
        self.offender_ipv4 = models.Offender(
            address='0.0.0.0',
            cidr=32,
            suggestion=False)
        self.offender_ipv6 = models.Offender(
            address='2001:dead:beef::',
            cidr=64)

    def test_cidrToNetmask(self):
        nt.assert_equal(self.offender_ipv4.netmask, '255.255.255.255')

    def test_find_create_from_ip_find(self):
        self.offender_ipv4.save()
        output = models.Offender.find_create_from_ip(self.offender_ipv4.address)
        nt.assert_equal(self.offender_ipv4, output)
        
    def test_find_create_from_ip_create(self):
        offender = models.Offender.objects.filter(address=self.offender_ipv6.address)
        nt.assert_equal(offender.count(), 0)
        output = models.Offender.find_create_from_ip(self.offender_ipv6.address)
        nt.assert_equal(type(self.offender_ipv4), type(output))
        nb_offender = models.Offender.objects.filter(address=self.offender_ipv6.address).count()
        nt.assert_equal(nb_offender, 1)

class TestAttackScore(object):

    def setup(self):
        self.score_indicators = {
            'et_compromised_ips': 1,
            'severity': 7,
            'times_zlb_redirected': 0,
            'dshield_block': 0,
            'event_types': 1,
            'last_attackscore': 8,
            'times_bgp_blocked': 0,
            'times_zlb_blocked': 1
        }
        self.score_factors = {
            'et_compromised_ips': 1,
            'severity': 2,
            'times_zlb_redirected': 3,
            'dshield_block': 4,
            'event_types': 5,
            'last_attackscore': 6,
            'times_bgp_blocked': 7,
            'times_zlb_blocked': 8
        }
        self.attackscore = models.AttackScore()

    def test_compute_attackscore(self):
        score_details = self.attackscore.compute_attackscore(
            self.score_indicators, self.score_factors)
        nt.assert_equal(score_details, {
            'dshield_block': 0,
            'et_compromised_ips': 1,
            'event_types': 5,
            'last_attackscore': 48,
            'severity': 14,
            'times_bgp_blocked': 0,
            'times_zlb_blocked': 8,
            'times_zlb_redirected': 0,
            'total': 76}
        )

class TestAttackScoreHistory(object):

    def setup(self):
        event = models.Event(
            attackerAddress='0.0.0.0',
            rulename='My Rule 1',
            severity=3,
            eventId=1234,
            attackerUserName='user',
        )
        event.save()

    def test_score_indicators(self):
        event = models.Event(
            attackerAddress='0.0.0.0',
            rulename='My Rule 2',
            severity=4,
            eventId=4321
        )
        event.save()
        offender = models.Offender(address='0.0.0.0', cidr=32)
        score_indicators = models.AttackScoreHistory.score_indicators(
            event, offender)
        nt.assert_equal(score_indicators, {
            'dshield_block': 0,
            'et_compromised_ips': 0,
            'event_types': 1,
            'last_attackscore': 0,
            'severity': 4,
            'times_bgp_blocked': 0,
            'times_zlb_blocked': 0,
            'times_zlb_redirected': 0}
        )

class TestWhitelistIP(object):
    
    def setup(self):
        whitelist = models.WhitelistIP(
            address='8.8.8.0',
            cidr=24,
            reporter="banhammer@locahost",
            comment="test"
        )
        whitelist.save()
    
    def test_is_ip_in(self):
        nt.assert_true(models.WhitelistIP.is_ip_in('8.8.8.8'))
        nt.assert_false(models.WhitelistIP.is_ip_in('6.6.6.6'))

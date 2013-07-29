from django_webtest import WebTest
from BanHammer.blacklist.tests import steps

class MenuTestCase(WebTest):
    def test_menu(self):
        index = self.app.get('/')
        assert '<h1>Blacklists</h1>' in index.click('Mozilla BanHammer-ng')
        assert '<h1>Offenders</h1>' in index.click('Offenders')
        # Blacklist & Show Expired Blacklists match
        assert '<h1>Blacklists</h1>' in index.click('Blacklists', index=1)
        # TODO: ZLBs
        assert '<h1>IP Whitelist</h1>' in index.click('IP Whitelist')
        # TODO: Mozilla Domain Whitelist
        assert '<h1>Settings</h1>' in index.click('Settings')

class BlacklistTestCase(WebTest):
    def test_index_empty(self):
        index = self.app.get('/blacklist/')
        assert '<h1>Blacklists</h1>' in index
        assert 'Address' in index
        assert 'CIDR' in index
        assert 'Type' in index
        assert 'Created' in index
        assert 'Expires' in index
        assert 'Reporter' in index
        assert 'No active blacklists.' in index

    def test_new_bgp_block(self):
        index = self.app.get('/blacklist/')
        new = index.click('BGP block')
        
        assert 'Apply a new network-wide blacklist' in new
        form = new.form
        form['target'] = '8.8.8.8/32'
        form['duration'] = '43200'
        form['start_date'] = '01/01/2013 01:00'
        form['end_date'] = '01/01/2013 13:00'
        form['comment'] = 'testlist'
        form['bug_number'] = '12345'
        
        index = form.submit().follow().follow()
        index = index.click('Show Expired Blacklists')
        assert '<h1>Blacklists</h1>' in index
        assert 'Hide Expired Blacklists' in index
        assert '8.8.8.8' in index
        assert 'BGP Blocked' in index
        assert '2013-01-01 01:01' in index
        assert '2013-01-01 13:01' in index
        assert 'test' in index
        assert not 'No active blacklists.' in index
        assert '<a href="https://bugzilla.mozilla.org/show_bug.cgi?id=12345">' in index

    def test_delete(self):
        self.test_new_bgp_block()
        index = self.app.get('/blacklist/show_expired')
        delete = index.click('<img src="/static/images/delete.gif">')
        index = delete.follow().follow()
        assert not '8.8.8.8' in index
        assert 'No active blacklists.' in index

class OffenderTestCase(WebTest):
    def test_index_empty(self):
        index = self.app.get('/offenders')
        assert '<h1>Offenders</h1>' in index
        assert 'Address' in index
        assert 'CIDR' in index
        assert 'Attack Score' in index
        assert 'Last Event' in index
        assert 'Created' in index
        assert 'No offenders.' in index
        index_suggestion = self.app.get('/offenders/show_suggested')
        assert '<h1>Offenders</h1>' in index_suggestion
        assert 'No offenders.' in index_suggestion

    def test_index_filled_blocked(self):
        steps.given_offender_blocked()
        index = self.app.get('/offenders')
        assert '8.8.8.8' in index
        assert '/32' in index
        index_suggestion = self.app.get('/offenders/show_suggested')
        assert '8.8.8.8' in index_suggestion
        assert '/32' in index_suggestion

    def test_index_filled_suggested(self):
        steps.given_offender_suggested()
        index = self.app.get('/offenders')
        assert 'No offenders.' in index
        index_suggestion = index.click('Show also offenders that have never been blocked yet')
        assert '4.2.2.1' in index_suggestion
        assert '/32' in index_suggestion
        assert '30' in index_suggestion

    def test_show_blocked(self):
        steps.given_offender_blocked()
        index = self.app.get('/offenders')
        show = index.click('8.8.8.8')
        # Title
        assert '<h1>Offender 8.8.8.8/32</h1>' in show.body
        assert '<h2>Score: </h2>' in show.body
        
        # Blacklist
        assert 'BGP Blocked' in show.body
        assert '2013-01-01 01:01' in show.body
        assert '2013-01-01 13:01' in show.body
        assert 'test@example.com' in show.body
        assert '<a href="https://bugzilla.mozilla.org/show_bug.cgi?id=12345">' in show.body
        assert '<img src="/static/images/comment.gif">' in show.body
        assert '<td colspan="5">testlist</td>' in show.body
        
        # Offender
        assert 'Address: 8.8.8.8' in show.body
        assert 'CIDR: 32' in show.body
        assert '<li>hostname: </li>' in show.body
        assert '<li>ASN: </li>' in show.body
        assert 'Created:' in show.body
        assert 'Updated:' in show.body
        
        # Event
        assert 'No events.' in show.body
    
    def test_show_suggested(self):
        steps.given_offender_suggested()
        index = self.app.get('/offenders')
        assert not '4.2.2.1' in index
        index = index.click('Show also offenders that have never been blocked yet')
        show = index.click('4.2.2.1')
        
        # Title
        assert '<h1>Offender 4.2.2.1/32</h1>' in show.body
        assert '<h2>Score: 30</h2>' in show.body
        
        # Blacklist
        assert 'No blacklists.' in show.body
        
        # Offender
        assert 'Address: 4.2.2.1' in show.body
        assert 'CIDR: 32' in show.body
        assert '<li>hostname: </li>' in show.body
        assert '<li>ASN: </li>' in show.body
        assert 'Created:' in show.body
        assert 'Updated:' in show.body
        
        # Event
        assert 'Test Rule (+5)' in show.body
        assert '2 (+10)' in show.body
        assert '30' in show.body
        assert '876781' in show.body
        assert '<li>attackerUserName: Script Kiddie</li>' in show.body
        # Score
        assert 'th>Element</th>' in show.body
        assert 'th>Value</th>' in show.body
        assert 'th>Score</th>' in show.body
        assert '<td>Severity</td>' in show.body
        assert show.body.count('<td>2</td>') == 2
        assert '<td>Different Event Types</td>' in show.body
        assert '<td>4</td>' in show.body
        assert '<td>8</td>' in show.body
        assert '<td>Number of times network-wide blocked with BGP blackholing</td>' in show.body
        assert show.body.count('<td>0</td>') == 10
        assert '<td>Number of times ZLB blocked</td>' in show.body
        assert '<td>Number of times ZLB redirected</td>' in show.body
        assert '<td>Last attack score</td>' in show.body
        assert '<td>Offender on Emerging Threat compromised IPs list</td>' in show.body
        assert '<td>Offender on DShield block list</td>' in show.body

    def test_edit(self):
        steps.given_offender_blocked()
        index = self.app.get('/offenders')
        show = index.click('8.8.8.8')
        edit = show.click('<i class="icon-pencil icon-legend"></i>')
        form = edit.form
        
        form['hostname'] = 'trololo.lol.com'
        form['asn'] = 42
        
        show = form.submit().follow()
        assert '<li>hostname: trololo.lol.com</li>' in show.body
        assert '<li>ASN: 42</li>' in show.body

class IPWhitelistTestCase(WebTest):
    fixtures = ['initial_data.json']

    def test_index(self):
        index = self.app.get('/whitelistip')

        assert 'Address' in index
        assert 'CIDR' in index
        assert 'Reporter' in index
        assert 'Created date' in index
        assert 'Updated date' in index
        
        assert '10.0.0.0' in index
        assert '/8' in index
        assert 'BanHammer-ng' in index
        assert '2013-01-01 00:01:00' in index
        assert '<img src="/static/images/comment.gif">' in index
        assert 'Private IPv4 space RFC 1918' in index

    def test_edit(self):
        index = self.app.get('/whitelistip')
        edit = index.click('<i class="icon-pencil"></i>', index=1)
        form = edit.form
        form['address'] = '1.2.3.4/32'
        form['comment'] = 'Test comment'
        index = form.submit().follow()
        assert '1.2.3.4' in index
        assert '/32' in index
        assert 'Test comment' in index

    def test_add(self):
        index = self.app.get('/whitelistip')
        add = index.click('Add new whitelisted IPs')
        form = add.form
        form['address'] = '4.3.2.1/32'
        form['comment'] = 'Test comment'
        index = form.submit().follow()
        assert '4.3.2.1' in index
        assert '/32' in index
        assert 'Test comment' in index

class SettingsTestCase(WebTest):
    fixtures = ['initial_data.json']

    def test_index(self):
        index = self.app.get('/settings')

        assert 'Enable email notifications' in index
        assert 'Expeditor address for email notifications' in index
        assert 'Recipient address for email notifications' in index
        assert 'Enable IRC notifications' in index
        assert 'Threshold for notifications of offenders' in index
        assert 'Factor for <strong>severity</strong> field in events' in index
        assert 'Factor for <strong>different types of past events</strong>' in index
        assert 'Factor for number of times the offender has been already <strong>blocked network-wide (BGP blackholing)</strong>' in index
        assert 'Factor for number of times the offender has been already <strong>blocked on ZLBs</strong>' in index
        assert 'Factor for number of times the offender has been already <strong>redirected on ZLBs</strong>' in index
        assert 'Factor for the <strong>last attack score</strong>' in index
        assert 'matching the IP on Emerging Threat' in index
        assert 'matching the IP on DShield.org' in index
    
    def test_edit(self):
        index = self.app.get('/settings')
        form = index.form
        
        form['notifications_email_enable'] = 'off'
        form['notifications_email_address_from'] = 'from@example.com'
        form['notifications_email_address_to'] = 'to@example.com'
        form['notifications_irc_enable'] = 'off'
        form['blacklist_unknown_threshold'] = '10'
        form['score_factor_severity'] = '11'
        form['score_factor_event_types'] = '12'
        form['score_factor_times_bgp_blocked'] = '13'
        form['score_factor_times_zlb_blocked'] = '14'
        form['score_factor_times_zlb_redirected'] = '15'
        form['score_factor_last_attackscore'] = '16'
        form['score_factor_et_compromised_ips'] = '17'
        form['score_factor_dshield_block'] = '18'
        
        index = form.submit()
        index = self.app.get('/settings')
        
        assert '<input checked="checked" type="checkbox" name="notifications_email_enable" id="id_notifications_email_enable" />' in index
        assert 'name="notifications_email_address_from" value="from@example.com"' in index
        assert 'name="notifications_email_address_to" value="to@example.com"' in index
        assert '<input checked="checked" type="checkbox" name="notifications_irc_enable" id="id_notifications_irc_enable" />' in index
        assert 'name="blacklist_unknown_threshold" value="10"' in index
        assert 'name="score_factor_severity" value="11"' in index
        assert 'name="score_factor_event_types" value="12"' in index
        assert 'name="score_factor_times_bgp_blocked" value="13"' in index
        assert 'name="score_factor_times_zlb_blocked" value="14"' in index
        assert 'name="score_factor_times_zlb_redirected" value="15"' in index
        assert 'name="score_factor_last_attackscore" value="16"' in index
        assert 'name="score_factor_et_compromised_ips" value="17"' in index
        assert 'name="score_factor_dshield_block" value="18"' in index

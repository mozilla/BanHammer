from django_webtest import WebTest

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
    def test_index(self):
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
        print index.__dict__
        print index.body
        assert not '8.8.8.8' in index
        assert 'No active blacklists.' in index

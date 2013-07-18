from django.core.management.base import BaseCommand, CommandError
from BanHammer import settings

import urllib2
import re

class Command(BaseCommand):
    help = 'Update 3rd party rules (et and dshield)'
    
    def handle(self, *args, **options):
        self._et_compromised_ips()
        self._dshield_block()

    def _et_compromised_ips(self):
        url = urllib2.urlopen(settings.ET_COMPROMISED_IPS_URL)
        f = open('%s/%s' % (settings.THIRD_PARTY_RULES_FOLDER, settings.ET_COMPROMISED_IPS_CONTENT_FILE), 'w')
        f.write(url.read())
        f.close()
        
        url = urllib2.urlopen(settings.ET_COMPROMISED_IPS_REV)
        f = open('%s/%s' % (settings.THIRD_PARTY_RULES_FOLDER, settings.ET_COMPROMISED_IPS_REV_FILE), 'w')
        f.write(url.read())
        f.close()
    
    def _dshield_block(self):
        url = urllib2.urlopen(settings.DSHIELD_BLOCK_URL)
        f = open('%s/%s' % (settings.THIRD_PARTY_RULES_FOLDER, settings.DSHIELD_BLOCK_CONTENT_FILE), 'w')
        content = url.read()
        networks = ''
        for l in content.splitlines():
            res = re.search('^(\d+\.\d+.\d+\.\d+)\t(\d+\.\d+.\d+\.\d+)\t(\d+)\t', l)
            if res:
                networks += '%s/%s\n' % (res.group(1), res.group(3))
        f.write(networks)
        f.close()
        
        f = open('%s/%s' % (settings.THIRD_PARTY_RULES_FOLDER, settings.DSHIELD_BLOCK_REV_FILE), 'w')
        rev = re.search('updated: (.*)\n', content, re.IGNORECASE).group(1)
        f.write(rev)
        f.close()

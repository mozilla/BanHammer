from django.core.management.base import BaseCommand, CommandError

import urllib2
import re

STORE_FOLDER = '/usr/local/third_party_ips'
 
ET_COMPROMISED_IPS_URL = 'https://rules.emergingthreatspro.com/blockrules/compromised-ips.txt'
ET_COMPROMISED_IPS_REV = 'https://rules.emergingthreatspro.com/blockrules/COMPrev'
ET_COMPROMISED_IPS_CONTENT_FILE = 'et_compromised_ips'
ET_COMPROMISED_IPS_REV_FILE = 'et_compromised_ips.rev' 

DSHIELD_BLOCK_URL = 'https://isc.sans.edu/block.txt'
DSHIELD_BLOCK_CONTENT_FILE = 'dshield_block'
DSHIELD_BLOCK_REV_FILE = 'dshield_block.rev'

class Command(BaseCommand):
    help = 'Update 3rd party rules (et and dshield)'
    
    def handle(self, *args, **options):
        self._et_compromised_ips()
        self._dshield_block()

    def _et_compromised_ips(self):
        url = urllib2.urlopen(ET_COMPROMISED_IPS_URL)
        f = open('%s/%s' % (STORE_FOLDER, ET_COMPROMISED_IPS_CONTENT_FILE), 'w')
        f.write(url.read())
        f.close()
        
        url = urllib2.urlopen(ET_COMPROMISED_IPS_REV)
        f = open('%s/%s' % (STORE_FOLDER, ET_COMPROMISED_IPS_REV_FILE), 'w')
        f.write(url.read())
        f.close()
    
    def _dshield_block(self):
        url = urllib2.urlopen(DSHIELD_BLOCK_URL)
        f = open('%s/%s' % (STORE_FOLDER, DSHIELD_BLOCK_CONTENT_FILE), 'w')
        content = url.read()
        networks = ''
        for l in content.splitlines():
            res = re.search('^(\d+\.\d+.\d+\.\d+)\t(\d+\.\d+.\d+\.\d+)\t(\d+)\t', l)
            if res:
                networks += '%s/%s\n' % (res.group(1), res.group(3))
        f.write(networks)
        f.close()
        
        f = open('%s/%s' % (STORE_FOLDER, DSHIELD_BLOCK_REV_FILE), 'w')
        rev = re.search('updated: (.*)\n', content, re.IGNORECASE).group(1)
        f.write(rev)
        f.close()

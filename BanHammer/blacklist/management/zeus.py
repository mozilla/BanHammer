import SOAPpy

from BanHammer import settings

class ZLB(object):
    def __init__(self, hostname, login, password):
        self.login = login
        self.password = password
        self.hostname = hostname
    
    def connect(self, wsdl):
        endpoint_uri = 'https://%s:%s@%s:9090/soap' % (self.login, self.password, self.hostname)
        self.conn = SOAPpy.WSDL.Proxy('%s/%s.wsdl' % (settings.WSDL, wsdl))
        for method in self.conn.methods.keys():
            self.conn.methods[method].location = endpoint_uri

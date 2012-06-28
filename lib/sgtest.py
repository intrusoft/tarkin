import random
import string
import time


from sshtest import SSHInstanceTest
from sshutils import SSHCommand

class SGTest(SSHInstanceTest):
    def __init__(self):
        print "SGTest.__init__"
        SSHInstanceTest.__init__(self)

    def rndstr(self, sz=10):
        return ''.join([random.choice(string.ascii_lowercase+string.digits) for _ in range(sz)])

    def create_group(self, name):
        self.create_sg_group(name, name)

    def delete_group(self, name):
        self.delete_sg_group(name)

    def auth_from_group(self, name, src_group, proto, to_port, from_port):
        self.auth_sg_group(name, src_security_group_name=src_group, ip_protocol=proto, to_port=to_port, from_port=from_port)

    def auth_from_cidr(self, name, cidr, proto, to_port, from_port):
        self.auth_sg_group(name, cidr_ip=cidr, ip_protocol=proto, to_port=to_port, from_port=from_port)     
   
    def create_good_bad_dest(self):
        good_name = 'good_' + self.rndstr(6)
        bad_name = 'bad_' + self.rndstr(6)
        dest_name = 'dest_' + self.rndstr(6)
        self.create_group(good_name)
        self.create_group(bad_name)
        self.create_group(dest_name)
        return (good_name, bad_name, dest_name)
   
    
if __name__ == '__main__':
    g = SGTest()
    (gd,bd,ds) = g.create_good_bad_dest()
    time.sleep(5)
    #g.auth_from_cidr(gd, '4.4.4.0/24', 'tcp', '22', '22')
    g.auth_from_group(gd, bd, 'tcp', '23', '23')
    #g.delete_group(gd)
    #g.delete_group(bd)
    g.delete_group(ds)

         

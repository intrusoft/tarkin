import random
import string
import time


from novatest import NovaEC2Test
from sshutils import SSHCommand

class SSHInstanceTest(NovaEC2Test):
    def __init__(self):
        print "SSHInstanceTest.__init__"
        NovaEC2Test.__init__(self)
        self.kp_path = None
        self.connect_api()
        
    def get_new_key_pair(self):
        kn = 'tk'+''.join([random.choice(string.ascii_lowercase+string.digits) for _ in range(8)])
        kp =  self.create_key_pair(kn)
        kp.save('/tmp/')
        return kn

    def setup_pingable_instance(self, key_name=None):
        """ This implementation waits till VM is pingable """

        # insert key shit
        print "launch"
        instance = self.launch_instance(key_name=key_name)
        if self.block_until_running(instance) and self.block_until_ping(instance):
            print "vm is pinging"
            return instance
        else:
            print "vm not responding"
            return None

    def ssh_cmd_simple(self, instance, key_name, cmd):
        ssh = SSHCommand('/tmp/%s.pem' % key_name)
        return ssh.cmdexec(instance.private_ip_address, cmd)

    # todo: cleanup the /tmp files        
    
if __name__ == '__main__':
    s = SSHInstanceTest()
    kn = s.get_new_key_pair()
    i = s.setup_pingable_instance(key_name=kn)
    time.sleep(5)
    print s.ssh_cmd_simple(i, kn, 'uptime')

    #print "sleeping"
    #time.sleep(60)
    #print "terminate"
    #i.terminate()


         

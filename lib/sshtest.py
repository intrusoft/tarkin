import random
import string
import time


from novatest import NovaEC2Test
from sshutils import SSHCommand

class SSHInstanceTest(NovaEC2Test):
    def __init__(self):
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
        instance = self.launch_instance(key_name=key_name)
        if self.block_until_running(instance) and self.block_until_ping(instance):
            self.log('instance %s is pingable' % instance.id)
            return instance
        else:
            self.log('instance %s is NOT pingable' % instance.id)
            return None

    def ssh_cmd_simple(self, instance, key_name, cmd):
        ssh = SSHCommand('/tmp/%s.pem' % key_name)
        self.log('Sennding command [%s] to %s' % (cmd, instance.private_ip_address))
        return ssh.cmdexec(instance.private_ip_address, cmd)

    # todo: cleanup the /tmp files        
    


         

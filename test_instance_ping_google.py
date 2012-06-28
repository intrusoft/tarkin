import re
import time
from lib.sshtest import SSHInstanceTest

class InstancePingGoogle(SSHInstanceTest):
    def main(self):
        _ping_ip_result = False
        _ping_dns_result = False
        keyname = self.get_new_key_pair()
        self.log('Set up instance')
        instance = self.setup_pingable_instance(keyname)
        if instance:
           time.sleep(5)
           output = self.ssh_cmd_simple(instance, keyname, 'ping -c 1 8.8.8.8')
           self.log(output)
           if '1 receive' in "".join(output):
               _ping_ip_result = True

           output = self.ssh_cmd_simple(instance, keyname, 'ping -c 1 google-public-dns-a.google.com')           
           self.log(output)
           if '1 receive' in "".join(output):
               _ping_dns_result = True

           self.terminate(instance)
           self.delete_key_pair(keyname)
           # delete keypair
        self.add_result(test_name=self.__class__.__name__+'_ping_ip', result=_ping_ip_result)
        self.add_result(test_name=self.__class__.__name__+'_ping_dns', result=_ping_dns_result)

if __name__ == '__main__':
    o = InstancePingGoogle()
    o.main()
    o.emit_results()


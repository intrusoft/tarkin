import re
import time
from lib.sshtest import SSHInstanceTest

class InstanceCorrectIP(SSHInstanceTest):
    def main(self):
        _result = False
        keyname = self.get_new_key_pair()
        instance = self.setup_pingable_instance(keyname)
        if instance:
           time.sleep(5)
           output = self.ssh_cmd_simple(instance, keyname, 'ifconfig eth0')
           if output:
               ifconfig_out = "\n".join(output)
               m = re.search('inet addr:([0-9\.]+)', ifconfig_out)
               if m:
                   detected_ip = m.groups()[0]
                   print "detected ip: %s " % detected_ip
                   if detected_ip == instance.private_ip_address:
                       _result = True
           print output
           
           self.terminate(instance)
           self.delete_key_pair(keyname)
           # delete keypair
        self.add_result(test_name=self.__class__.__name__, result=_result)

if __name__ == '__main__':
    o = InstanceCorrectIP()
    o.main()
    o.emit_results()


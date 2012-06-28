import re
import time
from lib.sshtest import SSHInstanceTest

class L3InstanceNetworkSettings(SSHInstanceTest):
    def _grab_pattern(self, needle, haystack):
        m = re.search(needle, haystack)
        if m:
            return m.groups()[0]

    def main(self):
        detected_ip = None
        detected_mask = None
        detected_broadcast = None
        detected_mac = None
        detected_default_gw = None
        ping_resule = False

        keyname = self.get_new_key_pair()
        self.log("Set up instance")
        instance = self.setup_pingable_instance(keyname)
        if instance:
           time.sleep(5)
           self.log("Query instance network settings")
           output = self.ssh_cmd_simple(instance, keyname, 'ifconfig eth0')
           self.log(output)
           if output:
               detected_ip = self._grab_pattern('inet addr:([0-9\.]+)', "".join(output))
               self.log("detected_ip: %s " % detected_ip)
               detected_mask = self._grab_pattern('Mask:([0-9\.]+)', "".join(output))
               self.log("detected_mask: %s " % detected_mask)
               detected_broadcast = self._grab_pattern('Bcast:([0-9\.]+)', "".join(output))
               self.log("detected_broadcast: %s " % detected_broadcast)
               detected_mac = self._grab_pattern('HWaddr ([0-9a-fA-F\:]+)', "".join(output))
               self.log("detected_mac: %s " % detected_mac)
           
           self.log("Get routing table")
           output = self.ssh_cmd_simple(instance, keyname, 'route -n')
           self.log(output)
           if output:
               detected_default_gw = self._grab_pattern('\n0.0.0.0\s+([0-9\.]+)', "".join(output))
               self.log("detected_default_gw: %s " % detected_default_gw)
               output = self.ssh_cmd_simple(instance, keyname, 'ping -c 1 %s' % detected_default_gw)           
               self.log(output)
               if '1 receive' in "".join(output):
                   self.log('default gw pingable')
                   _ping_dns_result = True

           # do evals
           _result = detected_ip == instance.private_ip_address
           self.add_result(test_name=self.__class__.__name__+'_correct_ip', result=_result)
            
           _result = '255.255.255.252' == detected_mask
           self.add_result(test_name=self.__class__.__name__+'_correct_netmask', result=_result)
           
           b = instance.private_ip_address.split('.')
           expected_broadcast = "%s.%s.%s.%d" % (b[0], b[1], b[2], int(b[3])+1)
           _result = expected_broadcast == detected_broadcast
           self.add_result(test_name=self.__class__.__name__+'_correct_broadcast', result=_result)

           expected_mac = '02:aa:' + ":".join([ ("%.2x"%int(x)) for x in instance.private_ip_address.split('.')])
           _result = expected_mac == detected_mac
           self.add_result(test_name=self.__class__.__name__+'_correct_mac', result=_result)   

           b = instance.private_ip_address.split('.')
           expected_gw = "%s.%s.%s.%d" % (b[0], b[1], b[2], int(b[3])-1)
           _result = expected_gw == detected_default_gw
           self.add_result(test_name=self.__class__.__name__+'_correct_gw', result=_result)

           self.add_result(test_name=self.__class__.__name__+'_ping_gw', result=_ping_dns_result)           

           self.terminate(instance)
           self.delete_key_pair(keyname)
           # delete keypair
        #self.add_result(test_name=self.__class__.__name__, result=_result)

if __name__ == '__main__':
    o = L3InstanceNetworkSettings()
    o.main()
    o.emit_results()


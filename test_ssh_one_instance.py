import time
from lib.sshtest import SSHInstanceTest

class SSHOneInstance(SSHInstanceTest):
    def main(self):
        _result = False
        keyname = self.get_new_key_pair()
        instance = self.setup_pingable_instance(keyname)
        if instance:
           time.sleep(5)
           output = self.ssh_cmd_simple(instance, keyname, 'uptime')
           if output:
               if 'load average' in "\n".join(output):
                   _result = True
           print output
           
           self.terminate(instance)
           self.delete_key_pair(keyname)
           # delete keypair
        self.add_result(test_name=self.__class__.__name__, result=_result)

if __name__ == '__main__':
    o = SSHOneInstance()
    o.main()
    o.emit_results()


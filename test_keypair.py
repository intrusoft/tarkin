import time
from lib.sshtest import SSHInstanceTest

class KeyPair(SSHInstanceTest):
    def main(self):
        _result = False
        keyname = self.get_new_key_pair()
        
        time.sleep(1)
        # list keys
        kps = self.get_all_key_pairs()
        if kps:
            kps_names = [x.name for x in kps]
            if keyname in kps_names:
                _result = True

        self.delete_key_pair(keyname)
        
        self.add_result(test_name=self.__class__.__name__, result=_result)

if __name__ == '__main__':
    o = KeyPair()
    o.main()
    o.emit_results()


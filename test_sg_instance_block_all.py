import re
import time
from lib.sgtest import SGTest

class SGInstanceBlockAll(SGTest):

    def main(self):
        _result = False
        tmp_group = 'tmp_' + self.rndstr(6)
        print "create group: %s" % tmp_group
        self.create_group(tmp_group)

        instance = self.launch_instance(security_groups=[tmp_group])

        # run instance with group
        
        if self.block_until_running(instance):
            if not self.block_until_ping(instance,timeout=25):
                _result = True

        self.add_result(test_name=self.__class__.__name__, result=_result)

        self.terminate(instance)

        # can't delete group when vm is still associated with it
        self.wait_for_terminated(instance)
        self.delete_group(tmp_group)       


if __name__ == '__main__':
    o = SGInstanceBlockAll()
    o.main()
    o.emit_results()


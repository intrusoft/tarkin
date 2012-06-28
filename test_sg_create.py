import re
import time
from lib.sgtest import SGTest

class SGCreate(SGTest):

    def main(self):
        tmp_group = 'tmp_' + self.rndstr(6)
        print "create group: %s" % tmp_group
        self.create_group(tmp_group)

        group_names = [x.name for x in  self.list_sg_groups()]
        print "list of groups: " , group_names

        _result = tmp_group in group_names
        self.add_result(test_name=self.__class__.__name__, result=_result)

        # remove the group
        self.delete_group(tmp_group)


if __name__ == '__main__':
    o = SGCreate()
    o.main()
    o.emit_results()


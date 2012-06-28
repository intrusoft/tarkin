import re
import time
from lib.sgtest import SGTest

class SGCreate(SGTest):

    def main(self):
        tmp_group = 'tmp_' + self.rndstr(6)
        self.log('creatin group: %s ' % tmp_group)
     
        sw = self.get_stopwatch()
        self.create_group(tmp_group)
        ellapsed_time = sw.stop()

        group_names = [x.name for x in  self.list_sg_groups()]
        self.log("list of groups: %s" % str(group_names) )

        _result = tmp_group in group_names
        self.add_result(test_name=self.__class__.__name__, result=_result, ellapsed_time=ellapsed_time)

        # remove the group
        time.sleep(1)
        self.delete_group(tmp_group)


if __name__ == '__main__':
    o = SGCreate()
    o.main()
    o.emit_results()


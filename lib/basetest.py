import json
import time

from stopwatch import StopWatch

class BaseTest:
    def __init__(self, log_file=None):
        self.results = []
        self.log_file = log_file
        self.log('Starting %s test' % self.__class__.__name__)

    def __del__(self):
        self.log('Ending %s test' % self.__class__.__name__)
        
    def add_result(self, **kwargs):
        result = {}
        for k in kwargs:
            result[k] = kwargs[k]
        self.results.append(result)
        self.log('Adding result: %s' % str(result))        

    def emit_results(self, format='human'):

        pass_fail = {True:'PASS', False:'FAIL'}

        if format == 'json':
            print json.dumps(self.results)

        if format == 'human':
            for r in self.results:
                extra = ",".join(["%s:%s"%(x,r[x]) for x in r.keys() if x not in ['result', 'test_name']])
                line = '%s %s (%s)' % (r['test_name'], pass_fail[r['result']], extra)
                print '%s' % line 

    def log(self, msg):
        if not self.log_file:
            self.log_file = self.__class__.__name__ + '.log'

        f = open(self.log_file, 'a+')
        _msg = "%d %s %s\n" % (time.time(), self.__class__.__name__, str(msg))
        f.write(_msg)
        f.close()

    def get_stopwatch(self):
        return(StopWatch())

    def main(self):
        print "Override this in your test"
                


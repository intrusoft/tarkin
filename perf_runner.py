
import glob
import inspect
import time
import traceback

from optparse import OptionParser
from operator import itemgetter

from eventlet import patcher
patcher.monkey_patch(all=True)
from eventlet import *

import sys

class PerfRunner:

    def run_test(self, test):
        mref = __import__(test)
        classes = inspect.getmembers(mref, inspect.isclass)
        for cname, c in classes:
            if c.__module__.startswith('test_'):
                tmp = c()
                try:
                    tmp.main()
                except Exception, e:
                    tmp.log(str(e))
                    tb = traceback.format_exc()
                    tmp.log(tb)
                    tmp.add_result(test_name=tmp.__class__.__name__, result=False, test_error=True)
                    print "# " + str(e)
                tmp.emit_results()
                self.total_tests -= 1

    def iterate_tests(self, test, iterations):
        for i in range(iterations):
            self.run_test(test)

    def launch_workers(self, test, iterations, workers):
        for w in range(int(workers)):
            spawn(self.iterate_tests, test, iterations)

    def run(self, tests, iterations, workers):
        all_tests = tests.split(',')
        self.total_tests = iterations * workers * len(all_tests)

        for test in all_tests:
            self.launch_workers(test, iterations, workers)

        while(self.total_tests > 0):
            time.sleep(1)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-t', '--tests', dest='tests', help='which tests to run, comma separated')
    parser.add_option('-i', '--iterations', dest='iterations', default='1', help='number of times to run each test')
    parser.add_option('-w', '--workers', dest='workers', default='1', help='workers')

    (options, args) = parser.parse_args()

    if options.tests:
        print "tests: %s" % options.tests    
        print "iterations: %s" % options.iterations
        print "workers: %s" % options.workers
        r = PerfRunner()
        r.run(options.tests, int(options.iterations), int(options.workers))
    else:
        print "Usage: perf_runner.py -t test_check_for_one_ami -i 10 -w 2" 
        print "       perf_runner.py -t <TEST_NAME> -i <ITERATIONS> -w <WORKERS>"




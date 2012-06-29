
import glob
import inspect
import traceback

class Runner:
    def run(self):
        mlist = glob.glob('test_*.py')
        fixed_mlist = [x[:-3] for x in mlist]
        for m in fixed_mlist:
            print "# Running: %s" % m
            mref = __import__(m)
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
        

if __name__ == '__main__':
    r = Runner()
    r.run()

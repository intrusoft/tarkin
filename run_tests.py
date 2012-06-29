
import glob
import inspect

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
                    tmp.main()
                    tmp.emit_results()
        

if __name__ == '__main__':
    r = Runner()
    r.run()

import json

class BaseTest:
    def __init__(self):
        print "base init"
        self.results = []
        pass

    def add_result(self, **kwargs):
        print "add_result"
        result = {}
        for k in kwargs:
            result[k] = kwargs[k]
        self.results.append(result)
        
    def emit_results(self, format='json'):
        if format == 'json':
            print json.dumps(self.results)
        else:
            print "Format '%s' not support" % format

    def main(self):
        print "Override this an implemente your test"
                
if __name__ == '__main__':
    b = BaseTest()
    b.add_result(result=False, time_elapsed=21)
    b.emit_results()


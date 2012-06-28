
from lib.novatest import NovaEC2Test

class CheckForOneAMI(NovaEC2Test):
    def main(self):
        self.connect_api()
        _result = False

        self.log('Calling get_images()')

        sw = self.get_stopwatch()
        images = self.get_images()
        time_taken = sw.stop()

        self.log('%d images returned from get_images()' % len(images))

        if len(images) > 0:
            _result = True
        
        self.add_result(test_name=self.__class__.__name__, result=_result, time_elapsed=time_taken)

if __name__ == '__main__':
    o = CheckForOneAMI()
    o.main()
    o.emit_results()


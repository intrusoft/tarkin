
from lib.novatest import NovaEC2Test

class CheckForOneAMI(NovaEC2Test):
    def main(self):
        self.connect_api()
        _result = False
        if len(self.get_images()) > 0:
            _result = True
        self.add_result(test_name=self.__class__.__name__, result=_result)

if __name__ == '__main__':
    o = CheckForOneAMI()
    o.main()
    o.emit_results()


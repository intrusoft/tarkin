
from lib.novatest import NovaEC2Test

class PingOneInstance(NovaEC2Test):
    def main(self):
        self.connect_api()
        _result = False
        instance = self.launch_instance()
        sw = self.get_stopwatch()
        time_till_ping = None
        if self.block_until_running(instance) and self.block_until_ping(instance):
            time_till_ping = sw.stop()
            _result = True
        self.add_result(test_name=self.__class__.__name__, result=_result, time_till_ping=time_till_ping)
        self.terminate(instance)

if __name__ == '__main__':
    o = PingOneInstance()
    o.main()
    o.emit_results()


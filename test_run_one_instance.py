
from lib.novatest import NovaEC2Test

class RunOneInstance(NovaEC2Test):
    def main(self):
        self.connect_api()
        instance = self.launch_instance()
        sw = self.get_stopwatch()
        self.add_result(test_name=self.__class__.__name__, result=self.block_until_running(instance), time_till_running=sw.stop())
        self.terminate(instance)

if __name__ == '__main__':
    o = RunOneInstance()
    o.main()
    o.emit_results()


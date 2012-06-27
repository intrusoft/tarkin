import boto
import json
import time

from basetest import BaseTest
import common as utils


# important eventlet stuff
from eventlet import patcher
patcher.monkey_patch(all=True)

DEFAULT_INSTANCE_TYPE = 'm1.tiny'

class NovaEC2Test(BaseTest):
    def __init__(self):
        print "NovaTest init"
        BaseTest.__init__(self)
        self.ec2_conn = None
        
        pass

    def connect_api(self):
        print "connect_api"
        self.ec2_conn = boto.connect_ec2(**utils.get_rc_credentials())

    def get_images(self):
        return self.ec2_conn.get_all_images()

    def get_first_ami(self):
        images = self.get_images()
        for i in images:
            if i.type == 'machine':
                return i

    def get_image(self, ami_name):
        return self.ec2_conn.get_image(ami_name)                

    def launch_instance(self, ami_name=None, inst_type=DEFAULT_INSTANCE_TYPE, key_name=None):
        if not ami_name:
            ami = self.get_first_ami()
        else:
            ami = self.get_image(ami_name)

        reservation = ami.run(instance_type=inst_type, key_name=key_name)
        print reservation.instances[0]
        return reservation.instances[0]

    def get_instance_status(self, instance):
        instance.update()
        return instance.state

    def block_until_running(self, instance, timeout=300):
        start_time = time.time()
        result = False
        while(time.time() < start_time + timeout):
            if self.get_instance_status(instance) == 'running':
                result = True
                break
            else:
                time.sleep(1)
        return result

    def block_until_ping(self, instance, timeout=300):
        start_time = time.time()
        result = False
        while(time.time() < start_time + timeout):
            if utils.checkping(instance):
                result = True
                break
            else:
                time.sleep(1)
        return result

    def terminate(self, instance):
        print "terminate: %r " % instance.id
        instance.terminate()

    def create_key_pair(self, name):
        return self.ec2_conn.create_key_pair(name)

    def delete_key_pair(self, name):
        return self.ec2_conn.delete_key_pair(name)
    
if __name__ == '__main__':
    n = NovaEC2Test()
    n.connect_api()
    n.create_key_pair('footest')
    """
    i = n.launch_instance()
    if n.block_until_running(i):
        print "Running"
        if n.block_until_ping(i):
            print "pingable"
            if n.block_until_ssh_ready(i, timeout=300):
                print "SSH ready"
            else:
                print "SSH Failed"
        else:
            print "not pingable!"
    else:
        print "Not Running"
    n.emit_results()
    """


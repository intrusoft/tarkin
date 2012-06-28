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

    def launch_instance(self, ami_name=None, inst_type=DEFAULT_INSTANCE_TYPE, key_name=None, security_groups=None):
        if not ami_name:
            ami = self.get_first_ami()
        else:
            ami = self.get_image(ami_name)

        reservation = ami.run(instance_type=inst_type, key_name=key_name, security_groups=security_groups)
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

    def create_sg_group(self, name, desc=None):
        return self.ec2_conn.create_security_group(name, desc)

    def delete_sg_group(self, name):
        return self.ec2_conn.delete_security_group(name)

    def auth_sg_group(self, name, src_security_group_name=None, cidr_ip=None,
                              ip_protocol=None, to_port=None, from_port=None):
        return self.ec2_conn.authorize_security_group(name, 
                                                 src_security_group_name=src_security_group_name, 
                                                 cidr_ip=cidr_ip, 
                                                 ip_protocol=ip_protocol,
                                                 to_port=to_port, 
                                                 from_port=from_port)
    def list_sg_groups(self):
        return self.ec2_conn.get_all_security_groups()

    def wait_for_terminated(self, instance, timeout=300):
        start = time.time()
        while(time.time() <= start+timeout): 
            if self.get_instance_status(instance) == 'terminated':
                break
            else:
                time.sleep(1)

    
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


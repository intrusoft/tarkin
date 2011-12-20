#!/usr/bin/env python

import os
import sys
import time

from lib.localutils import checkping
from lib.sshutils import SSHCommand


import boto
from boto.ec2.regioninfo import RegionInfo

KEY_PATH = '/root/test.pem'

# test how quick rules get applied to running VMs
# create tons of security groups until breaks

# FYI on a slow machine this test can take 5 - 10 minutes to complete

# Some sane defaults
INSTANCE_TYPE = 'm1.tiny'
REGION_NAME = 'test'
KEYPAIR_NAME = 'test'

_ami = 'ami-00000001'
_aki = 'aki-00000003'
_ari = 'ari-00000002'

start_time = time.time()

def _log(msg):
    line = "%d %s" % (int(time.time() - start_time), msg) 
    print line

class SGVerify():
    def __init__(self, region, awshost, awsaccesskey, awssecretkey, awsport):
        _log("Connecting to end-point")
        self.region = RegionInfo(None, region, awshost)
        self.ec2_conn = boto.connect_ec2(awsaccesskey,awssecretkey,
                                         region=self.region, 
                                         port=awsport, 
                                         is_secure=False, 
                                         path='/services/Cloud')

        self.ssh = SSHCommand(KEY_PATH)
   
    def _cleanup_stale_groups(self): 
        _log("Cleaning up stale security groups")
        try:
            self.ec2_conn.delete_security_group('destgrp')
        except Exception:
            pass
        try:
            self.ec2_conn.delete_security_group('evilgrp')
        except Exception:
            pass
        try:
            self.ec2_conn.delete_security_group('goodgrp')
        except Exception:
            pass


    def _create_groups(self):
        _log("Creating new groups")
        self.ec2_conn.create_security_group('destgrp', 'protected')
        self.ec2_conn.create_security_group('evilgrp', 'bad guys')
        self.ec2_conn.create_security_group('goodgrp', 'good guys')


    def _setup_rules(self):
        _log("Setup rules")
        self.ec2_conn.authorize_security_group('destgrp', 
                                               src_security_group_name='goodgrp', 
                                               ip_protocol='tcp', 
                                               to_port='22', 
                                               from_port='22')

        self.ec2_conn.authorize_security_group('evilgrp', 
                                               cidr_ip='0.0.0.0/0', 
                                               ip_protocol='tcp', 
                                               to_port='22', 
                                               from_port='22')

        self.ec2_conn.authorize_security_group('goodgrp', 
                                               cidr_ip='0.0.0.0/0', 
                                               ip_protocol='tcp', 
                                               to_port='22', 
                                               from_port='22')

    def _launch_vm(self, group_name):
        _log("Launching VM in %s group" % group_name)
        image = self.ec2_conn.get_image(_ami)
        reservation = image.run(kernel_id=_aki, 
                                ramdisk_id=_ari, 
                                instance_type=INSTANCE_TYPE, 
                                security_groups=[group_name], 
                                key_name=KEYPAIR_NAME)

        return reservation.instances[0]

    def _block_till_running(self, inst):
        _log("Waiting for instance %s to be in running state " % inst.id)
        result = False
        for x in range(60):
            inst.update()
            if inst.state == 'running':
                result = True
                break
            time.sleep(1)
        return result
        
    def _block_till_ping(self, host):
        _log("Waiting for instance %s to be pingable " % host)
        result = False
        for x in range(60):
            if checkping(host):
                result = True
                break
            time.sleep(1)
        return result

    def _instance_ping_out(self, ssh_host, host):
        #_log("Attempting to ping from %s to %s " % (ssh_host, host))
        buffer = self.ssh.cmdexec(ssh_host, 'ping -W 5 -q -n -c 1 %s' % host)
        if '1 received' in buffer[0]:
            return True
        else:
            return False

    def _instance_tcp_out(self, ssh_host, host, port):
        #_log("Attempting to reach %s:%d from %s " % (ssh_host, int(port), host))
        buffer = self.ssh.cmdexec(ssh_host, 'nc -v -d -v -z -w 1 %s %d ' % (host, int(port)) )
        if 'succeeded' in buffer[0]:
            return True
        else:
            return False

    def _instance_ssh_ready(self, ssh_host):
        _log("Waiting for SSH to be ready on %s " % ssh_host)
        result = False
        for x in range(120):
            buffer = self.ssh.cmdexec(ssh_host, 'uptime')
            if 'load average' in buffer[0]:
                result = True
                break
            time.sleep(5)
        return result
        

    def run(self):
        self._cleanup_stale_groups()

        time.sleep(1) # hack, but give nova some time to complete action

        self._create_groups()

        time.sleep(1)

        self._setup_rules()

        time.sleep(1)

        dest_inst = self._launch_vm('destgrp')

        time.sleep(1)

        good_inst = self._launch_vm('goodgrp')

        time.sleep(1)

        evil_inst = self._launch_vm('evilgrp')

        if not ( self._block_till_running(dest_inst) and
                 self._block_till_running(good_inst) and
                 self._block_till_running(evil_inst) ):
            _log("Error while waiting for instances to reach running state")
            return

        if not ( self._block_till_ping(dest_inst.public_dns_name) and
                 self._block_till_ping(good_inst.public_dns_name) and
                 self._block_till_ping(evil_inst.public_dns_name) ):
            _log("Error while waiting for instances to be pingable from this host")
            return

        if not (self._instance_ssh_ready(good_inst.public_dns_name) and
                self._instance_ssh_ready(evil_inst.public_dns_name) ):
            _log("Error while waiting for instances to be SSH'able")
            return

        _log("\n --- STARTING TESTS --- \n") 
 
        result = self._instance_ping_out(dest_inst.public_dns_name, '8.8.8.8')
        _log("dest instance %s (%s) can reach the public internet: %s" % (
            dest_inst.public_dns_name, dest_inst.id, result))

        result = self._instance_ping_out(good_inst.public_dns_name, '8.8.8.8')
        _log("good instance %s (%s) can reach the public internet: %s" % ( 
            good_inst.public_dns_name, good_inst.id, result))        

        result = self._instance_ping_out(evil_inst.public_dns_name, '8.8.8.8')
        _log("evil instance %s (%s) can reach the public internet: %s" % ( 
            evil_inst.public_dns_name, evil_inst.id, result))        

        result =  not self._instance_tcp_out(evil_inst.public_dns_name, dest_inst.public_dns_name, 22)
        _log("evil instance %s (%s) CAN't reach dest instance %s (%s) via SSH" % (
              evil_inst.public_dns_name, evil_inst.id, 
              dest_inst.public_dns_name, dest_inst.id))

        result = self._instance_tcp_out(good_inst.public_dns_name, dest_inst.public_dns_name, 22)
        _log("good instance %s (%s) CAN reach dest instance %s (%s) via SSH" % (
               good_inst.public_dns_name, good_inst.id,
               dest_inst.public_dns_name, dest_inst.id))

        result = self._instance_tcp_out(evil_inst.public_dns_name, good_inst.public_dns_name, 22)
        _log("evil instance %s (%s) CAN reach good instance %s (%s) via SSH" % (
              evil_inst.public_dns_name, evil_inst.id,
              good_inst.public_dns_name, good_inst.id))

        result = self._instance_tcp_out(good_inst.public_dns_name, evil_inst.public_dns_name, 22)
        _log("good instance %s (%s) CAN reach evil instance %s (%s) via SSH" % (
               good_inst.public_dns_name, good_inst.id,
               evil_inst.public_dns_name, evil_inst.id))
     
if __name__ == '__main__':
    if 'EC2_ACCESS_KEY' in os.environ and 'EC2_SECRET_KEY' in os.environ:
        AWS_ACCESS_KEY_ID = os.environ['EC2_ACCESS_KEY']
        AWS_SECRET_ACCESS_KEY = os.environ['EC2_SECRET_KEY']
        AWS_HOST = os.environ['EC2_URL'].split('/')[2].split(':')[0]
        AWS_PORT = int(os.environ['EC2_URL'].split('/')[2].split(':')[1])
        sg = SGVerify(REGION_NAME, AWS_HOST, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_PORT)
        sg.run()
    else:
        print "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY not set"
        print "You can do this by sourcing novarc or setting the environment variables"
        sys.exit()


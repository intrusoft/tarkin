#!/usr/bin/env python

import time

import lib.common as util
from lib.sshutils import SSHCommand


import boto

#TODO(jogo) remove default
KEY_PATH = '/root/test.pem'

# test how quick rules get applied to running VMs
# create tons of security groups until breaks

# FYI on a slow machine this test can take 5 - 10 minutes to complete

# Some sane defaults
INSTANCE_TYPE = 'm1.tiny'
KEYPAIR_NAME = 'test'

_ami = 'ami-00000002'

start_time = time.time()

class SGVerify():
    def __init__(self):
        util.log("Connecting to end-point")
        self.ec2_conn = boto.connect_ec2(**util.get_rc_credentials())

        self.ssh = SSHCommand(KEY_PATH)
   
    def _cleanup_stale_groups(self): 
        util.log("Cleaning up stale security groups")
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
        util.log("Creating new groups")
        self.ec2_conn.create_security_group('destgrp', 'protected')
        self.ec2_conn.create_security_group('evilgrp', 'bad guys')
        self.ec2_conn.create_security_group('goodgrp', 'good guys')


    def _setup_rules(self):
        util.log("Setup rules")

        # Added so block_till_ping works
        self.ec2_conn.authorize_security_group('destgrp', 
                                               ip_protocol='icmp', 
                                               to_port='-1', 
                                               from_port='-1')
        self.ec2_conn.authorize_security_group('evilgrp', 
                                               ip_protocol='icmp', 
                                               to_port='-1', 
                                               from_port='-1')
        self.ec2_conn.authorize_security_group('goodgrp', 
                                               ip_protocol='icmp', 
                                               to_port='-1', 
                                               from_port='-1')



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

    #TODO(jogo) move into lib
    def _launch_vm(self, group_name):
        util.log("Launching VM in %s group" % group_name)
        image = self.ec2_conn.get_image(_ami)
        reservation = image.run(instance_type=INSTANCE_TYPE, 
                                security_groups=[group_name], 
                                key_name=KEYPAIR_NAME)

        return reservation.instances[0]

    def _instance_ping_out(self, ssh_host, host):
        #util.log("Attempting to ping from %s to %s " % (ssh_host, host))
        buffer = self.ssh.cmdexec(ssh_host, 'ping -W 5 -q -n -c 1 %s' % host)
        if '1 received' in buffer[0]:
            return True
        else:
            return False

    def _instance_tcp_out(self, ssh_host, host, port):
        #util.log("Attempting to reach %s:%d from %s " % (ssh_host, int(port), host))
        buffer = self.ssh.cmdexec(ssh_host, 'nc -v -d -v -z -w 1 %s %d ' % (host, int(port)) )
        if 'succeeded' in buffer[0]:
            return True
        else:
            return False

    def _instance_ssh_ready(self, instance):
        util.log("%s status: Waiting for SSH " % instance.id)
        result = False
        for x in range(120):
            output = self.ssh.cmdexec(instance.private_ip_address, 'uptime')
            if 'load average' in output[0]:
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

        if not ( util.block_till_running(self,dest_inst) and
                 util.block_till_running(self,good_inst) and
                 util.block_till_running(self,evil_inst) ):
            return

        if not ( util.block_till_ping(self,dest_inst) and
                 util.block_till_ping(self,good_inst) and
                 util.block_till_ping(self,evil_inst) ):
            return

        if not (self._instance_ssh_ready(good_inst) and
                self._instance_ssh_ready(evil_inst) ):
            util.log("Error while waiting for instances to be SSH'able")
            return

        util.log("\n --- STARTING TESTS --- \n") 
 
        result = self._instance_ping_out(dest_inst.private_ip_address, '8.8.8.8')
        util.log("dest instance %s (%s) can reach the public internet: %s" % (
            dest_inst.private_ip_address, dest_inst.id, result))

        result = self._instance_ping_out(good_inst.private_ip_address, '8.8.8.8')
        util.log("good instance %s (%s) can reach the public internet: %s" % ( 
            good_inst.private_ip_address, good_inst.id, result))        

        result = self._instance_ping_out(evil_inst.private_ip_address, '8.8.8.8')
        util.log("evil instance %s (%s) can reach the public internet: %s" % ( 
            evil_inst.private_ip_address, evil_inst.id, result))        

        result =  not self._instance_tcp_out(evil_inst.private_ip_address, dest_inst.private_ip_address, 22)
        util.log("evil instance %s (%s) CAN't reach dest instance %s (%s) via SSH" % (
              evil_inst.private_ip_address, evil_inst.id, 
              dest_inst.private_ip_address, dest_inst.id))

        result = self._instance_tcp_out(good_inst.private_ip_address, dest_inst.private_ip_address, 22)
        util.log("good instance %s (%s) CAN reach dest instance %s (%s) via SSH" % (
               good_inst.private_ip_address, good_inst.id,
               dest_inst.private_ip_address, dest_inst.id))

        result = self._instance_tcp_out(evil_inst.private_ip_address, good_inst.private_ip_address, 22)
        util.log("evil instance %s (%s) CAN reach good instance %s (%s) via SSH" % (
              evil_inst.private_ip_address, evil_inst.id,
              good_inst.private_ip_address, good_inst.id))

        result = self._instance_tcp_out(good_inst.private_ip_address, evil_inst.private_ip_address, 22)
        util.log("good instance %s (%s) CAN reach evil instance %s (%s) via SSH" % (
               good_inst.private_ip_address, good_inst.id,
               evil_inst.private_ip_address, evil_inst.id))
     
if __name__ == '__main__':
    try:
        sg = SGVerify()
        sg.run()
    except Exception:
        print "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY not set"
        print "You can do this by sourcing novarc or setting the environment variables"

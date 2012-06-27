#!/usr/bin/env python

import os
import sys
import time

import boto

import lib.common as utils

# important eventlet stuff
from eventlet import patcher
patcher.monkey_patch(all=True)
from eventlet import *

# Some sane defaults
REGION_NAME = 'test'

from lib.sshutils import SSHCommand

KEY_PATH = '/root/test.pem'

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


def ping_vm():
    ami = 'ami-00000002'
    ec2_conn = boto.connect_ec2(**utils.get_rc_credentials())
    instance = utils.launch_vm(None, ec2_conn.get_image(ami))
    print "Instance: %s " % instance.id
    if instance.state == 'pending':
        if utils.block_till_running(None, instance, wait=300):
            print "Running"
            if utils.block_till_ping(None, instance):
                print "Pinging"

                # ssh into vm


            else:
                print "Never pinged"
            
            print "result: PASS"
        else:
            print "result: FALSE"
        print "terminating"
        instance.terminate()

if __name__ == '__main__':
    ping_vm()


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
            else:
                print "Never pinged"
            
            print "result: PASS"
        else:
            print "result: FALSE"
        print "terminating"
        instance.terminate()

if __name__ == '__main__':
    ping_vm()


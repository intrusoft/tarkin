#!/usr/bin/env python

"""

This script measures how long it takes to ping each running VM.

Designed to latency when restarting nova-networking

"""
import eventlet
import os
import sys
#import re
import time

import lib.localutils as utils

import boto
from boto.ec2.regioninfo import RegionInfo

eventlet.patcher.monkey_patch(all=True)

REGION_NAME = 'test'
KEYPAIR_NAME = 'test'


class PingAll():
    def __init__(self, region, awshost, awsaccesskey, awssecretkey, awsport):
        utils.log("Connecting to end-point")
	self._tests= []
        self.region = RegionInfo(None, region, awshost)
        self.ec2_conn = boto.connect_ec2(awsaccesskey, awssecretkey,
                                         region=self.region,
                                         port=awsport,
                                         is_secure=False,
                                         path='/services/Cloud')


    def async_ping(self,host):
        val = utils.block_till_ping(self,host,60);
        self._tests.append(val)

    def get_finished_tests(self):
        return len(self._tests)


    def wait_for_tests(self,count):
        current_count = 0
        while(True):    # loop until we are done with all the tests
            tests_run = self.get_finished_tests()
            if current_count < tests_run:
                print "Tests run: %d / %d " % (tests_run, count)
                current_count = tests_run
            
            if tests_run == count:
                break
            time.sleep(2)



    def run(self):
        #get list of running VMs
        reservations = self.ec2_conn.get_all_instances()
        count =  len(reservations)
        utils.log("%d VMs" % count)

        #ping each VM
        for reservation in reservations:
            for instance in reservation.instances:
                instance.update()
                if instance.state != 'running':
                    print "%s in bad state" % instance.public_dns_name
                    count = count - 1
                    continue
                #utils.log("start pinging %s"  % instance.public_dns_name)
                eventlet.spawn(self.async_ping,
                               instance.public_dns_name)

    
        #wait for tests
        self.wait_for_tests(count)


if __name__ == '__main__':
    if 'EC2_ACCESS_KEY' in os.environ and 'EC2_SECRET_KEY' in os.environ:
        AWS_ACCESS_KEY_ID = os.environ['EC2_ACCESS_KEY']
        AWS_SECRET_ACCESS_KEY = os.environ['EC2_SECRET_KEY']
        AWS_HOST = os.environ['EC2_URL'].split('/')[2].split(':')[0]
        AWS_PORT = int(os.environ['EC2_URL'].split('/')[2].split(':')[1])
        pa = PingAll(REGION_NAME, AWS_HOST, AWS_ACCESS_KEY_ID,
                     AWS_SECRET_ACCESS_KEY, AWS_PORT)
        pa.run()
    else:
        print "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY not set"
        print "set by sourcing novarc or setting the environment variables"
        sys.exit()

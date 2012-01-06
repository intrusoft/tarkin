#!/usr/bin/env python

"""

This script measures how long it takes to ping each running VM.

Designed to latency when restarting nova-networking

"""
import eventlet
import os
import sys
#import re
#import time

import lib.localutils as utils

import boto
from boto.ec2.regioninfo import RegionInfo

eventlet.patcher.monkey_patch(all=True)

REGION_NAME = 'test'
KEYPAIR_NAME = 'test'


class PingAll():
    def __init__(self, region, awshost, awsaccesskey, awssecretkey, awsport):
        utils.log("Connecting to end-point")
        self.region = RegionInfo(None, region, awshost)
        self.ec2_conn = boto.connect_ec2(awsaccesskey, awssecretkey,
                                         region=self.region,
                                         port=awsport,
                                         is_secure=False,
                                         path='/services/Cloud')

    def run(self):
        #get list of running VMs
        reservations = self.ec2_conn.get_all_instances()

        try:
            for reservation in reservations:
                for instance in reservation.instances:
                    instance.update()
                    if instance.state != 'running':
                        continue
                    #utils.log("start pinging %s"  % instance.public_dns_name)
                    eventlet.spawn(utils.block_till_ping, self,
                                   instance.public_dns_name, 9999)
        except (SystemExit, KeyboardInterrupt):
            return 0


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

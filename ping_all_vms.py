#!/usr/bin/env python

"""

This script measures how long it takes to ping each running VM.

Designed to measure latency when restarting nova-networking

"""
import boto
import eventlet

import lib.common as utils


eventlet.patcher.monkey_patch(all=True)

class PingAll():
    def __init__(self):
        utils.log("Connecting to end-point")
        self.ec2_conn = boto.connect_ec2(**utils.get_rc_credentials())

    def async_ping(self,instance):
        val = utils.block_till_ping(self,instance,999);
        utils.add_record(val)

    def run(self):
        #get list of running VMs
        reservations = self.ec2_conn.get_all_instances()
        count = 0 

        #ping each VM
        for reservation in reservations:
            for instance in reservation.instances:
                #instance.update()
                if instance.state != 'running':
                    utils.log("%s state: %s" % (instance.id,instance.state))
                    continue
                #utils.log("start pinging %s"  % instance.public_dns_name)
                count+=1
                eventlet.spawn(self.async_ping,
                               instance)

        utils.log("%d VMs" % count)
    
        #wait for tests
        utils.wait_for_tests(count)


if __name__ == '__main__':
    pa = PingAll()
    pa.run()

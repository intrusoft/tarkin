#!/usr/bin/env python

"""

This script will launch multiple VMs at a time. You can specify how many workers
and iterations. Workers go into a loop specified by the number of iterations. Each
iteration will spawn a VM, wait until it can be pinged and then terminates the vm.
For example, if you specify 4 workers and 10 iterations, you will end up creating
40 VMs, but only 10 at a time. 

This script shouldn't get too wild with testing other aspects of Nova. The intent
of this script is to try and break Nova due to race conditions and synchronization
bugs that could pop up in the network controller. Ideally this script would
be run with many workers over a long period of time. This should expose any bugs
in the form of stack traces in the nova logs, VMs failing to hit running state,
and VMs failing to ping. This script has already been able to reliably break
database code in diablo and cause kernel panics in our test ubuntu AMI.

This script assumes you have already augmented the default security group to
allow ICMP through

TODO:
    - When a VM fails to ping, grab the console output of the VM to detect
         meta-data, image or kernel panic issues.


"""

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

class vmrunner():

    def __init__(self, ami ):
        self._ami = ami

    def runner(self, workers, iterations, logfile):
        """ main loop function """
        try: 
            LOG = open(logfile, "w")
            LOG.write('Instance ID, Test Result, Run Time, Ping Time\n')
        except:
            print "opening %s failed!\n" % logfile 
            exit(1)
        for _ in range(workers):    # spawn a green-thread for each worker
            spawn(self.runx, iterations, LOG)

        utils.wait_for_tests(iterations * workers)
        LOG.close()
 
    def runx(self, iterations, LOG):
        """ loop for individual worker so it does the specified number of iterations """
        for _ in range(iterations):
            self.run(LOG)

    def run(self, LOG):
        """ function that starts all the tests """

        # connect to Nova
        ec2_conn = boto.connect_ec2(**utils.get_rc_credentials())

        # test data defaults
        test_result = False
        instance_id = 'unknown'
        run_time = -1
        ping_time = -1

        # with the image reference we spawn an image from it
        instance = utils.launch_vm(self,ec2_conn.get_image(ami))
        start_time = time.time()
        instance_id = instance.id

        if instance.state == 'pending':    # VM is on its way
            utils.log("%s state: pending" % instance_id)
	    if utils.block_till_running(self,instance):
                run_time = utils.elapsed_time(start_time)
                # ping till up
		if utils.block_till_ping(self,instance,600):
                    ping_time = utils.elapsed_time(start_time)
                    utils.log("%s state: terminating" % instance_id)
                    test_result = True
                    instance.terminate()
        else:
            utils.log("%s Unexpected state in VM after run() %r" % (instance_id, instance.state))
        utils.add_record( {'id': instance_id, 'test_result': test_result, 'run_time': run_time, 'ping_time': ping_time}  )     
        data = "%s, %s, %s, %s\n" % (instance_id, test_result, run_time, ping_time)
        LOG.write(data)
        
if __name__ == '__main__':
    try:
        if len(sys.argv) > 4: 
            ami = sys.argv[4]
	else: raise Exception()
        vm = vmrunner(ami)
        vm.runner(int(sys.argv[1]), int(sys.argv[2]), str(sys.argv[3]))
    except Exception:
        print "Usage: ./vm_runner.py number_of_workers number_of_iterations logfile ami"
        print "Make sure you have sourced novarc to set env variables"
        exit(1)
    print "\n" 
    for x in utils.get_records():
        print x

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
from boto.ec2.regioninfo import RegionInfo

# important eventlet stuff
from eventlet import patcher
patcher.monkey_patch(all=True)
from eventlet import *

# Some sane defaults
INSTANCE_TYPE = 'm1.tiny'
REGION_NAME = 'test'
RUN_TIMEOUT = 60
PING_TIMEOUT = 120

class vmrunner():

    def __init__(self, ami=None, aki=None, ari=None):
        self._tests = []
        if ami:
            self._ami = ami
            self._aki = aki 
            self._ari = ari
        else:
            # some defaults if an AMI is not specified
            self._ami = 'ami-00000001'
            self._aki = 'aki-00000003'
            self._ari = 'ari-00000002'

    def _checkping(self, host):
        if os.system("ping -c 1 %s > /dev/null" % host) == 0:
            return True
        else:
            return False

    def _delta(self, start, end):
        return int(end - start)

    def record_test(self, testinfo):
        self._tests.append(testinfo)

    def get_tests(self):
        return self._tests

    def runner(self, workers, iterations):
        """ main loop function """

        for _ in range(workers):    # spawn a green-thread for each worker
            spawn(self.runx, iterations)

        while(True):    # loop until we are done with all the tests
            tests_run = len(self.get_tests())
            print "Tests run: %d / %d " % (tests_run, iterations * workers)
            
            if tests_run == iterations * workers:
                break
            time.sleep(5)

    def runx(self, iterations):
        """ loop for individual worker so it does the specified number of iterations """
        for _ in range(iterations):
            self.run()

    def run(self):
        """ function that starts all the tests """

        # connect to Nova
        region = RegionInfo(None, REGION_NAME, AWS_HOST)
        ec2_conn = boto.connect_ec2(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, region=region, port=AWS_PORT, is_secure=False, path='/services/Cloud')

        # get a list of images and find the one we care about
        images = ec2_conn.get_all_images()


        # test data defaults
        test_result = False
        instance_id = 'unknown'
        run_time = -1
        ping_time = -1

        for image in images:

            if image.id == self._ami:

                # with the image reference we spawn an image from it
                reservation = image.run(kernel_id=self._aki, ramdisk_id=self._ari, instance_type=INSTANCE_TYPE)

                start_time = time.time()
                instance = reservation.instances[0]
                instance_id = instance.id

                if instance.state == 'pending':    # VM is on its way
                    print "%s state: pending" % instance_id

                    for x in range(RUN_TIMEOUT):   # wait for VM to go from pending to running
                        time.sleep(1)
                        instance.update()
                        if instance.state == 'running':
                            run_time = self._delta(start_time, time.time())  
                            break
                    if instance.state == 'running':    # wait for VM to be pingable
                        print "%s state: running" % instance_id
                        # ping till up
                        for x in range(PING_TIMEOUT):
                            time.sleep(1)
                            if self._checkping(instance.public_dns_name):
                                ping_time = self._delta(start_time, time.time())
                                break
                        if self._checkping(instance.public_dns_name):
                            print "%s state: pingable" % instance_id
                            print "%s Time till Runnning: %d, Time till Ping: %d " % (instance.id, run_time, ping_time) 
                            print "%s terminating instance" % instance_id
                            test_result = True
                            try:
                                instance.stop()   # bug in boto, exception is always triggered here
                            except Exception, e:
                                pass
                        else:
                            print "%s VM fails to ping after specified period of time" % instance_id
                              
                    else:
                        print "%s Failed to reach running state" % instance_id             
 
                else:
                    print "%s Unexpected state in VM after run() %r" % (instance_id, instance.state)
        self.record_test( {'id': instance_id, 'test_result': test_result, 'run_time': run_time, 'ping_time': ping_time}  )     
        
if __name__ == '__main__':
    if 'EC2_ACCESS_KEY' in os.environ and 'EC2_SECRET_KEY' in os.environ:
        AWS_ACCESS_KEY_ID = os.environ['EC2_ACCESS_KEY']
        AWS_SECRET_ACCESS_KEY = os.environ['EC2_SECRET_KEY']
        AWS_HOST = os.environ['EC2_URL'].split('/')[2].split(':')[0]
        AWS_PORT = int(os.environ['EC2_URL'].split('/')[2].split(':')[1])

    else:
        print "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY not set"
        print "You can do this by sourcing novarc or setting the environment variables"
        sys.exit()

    if len(sys.argv) > 2:
            
        ami = None
        aki = None
        ari = None

        if len(sys.argv) > 3: 
            ami = sys.argv[3]
        if len(sys.argv) > 4:
            aki = sys.argv[4]
        if len(sys.argv) > 5:
            ari = sys.argv[5]

        vm = vmrunner(ami, aki, ari)
        vm.runner(int(sys.argv[1]), int(sys.argv[2]))
        print "\n\n" 
        for x in vm.get_tests():
            print x
    else:
        print "Usage: ./vm_runner.py number_of_workers number_of_iterations [ami] [aki] [ari]"
        print "Make sure you have sourced novarc to set env variables"
  



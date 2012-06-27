#!/usr/bin/env python

"""

This script will generate multiple keypairs at a time.  You can specify how 
many workers and iterations. Workers go into a loop specified by the number 
of iterations. Each iteration generates a key makes sure it shows up in list 
and deletes it.

Goal is to test out nova-cert service

NOTE: Found bug, when keyname starts with a 0 nova stack traces

"""

import sys
import boto
import string
import random

import lib.common as utils

# important eventlet stuff
from eventlet import patcher
patcher.monkey_patch(all=True)
from eventlet import *

# Some sane defaults
REGION_NAME = 'test'

class keyrunner():

    def random_name(self,length):
      return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(length))
  
    def runner(self, workers, iterations):
        """ main loop function """

        for _ in range(workers):    # spawn a green-thread for each worker
            spawn(self.runx, iterations)

        utils.wait_for_tests(iterations * workers)

    def runx(self, iterations):
        """ loop for individual worker so it does the specified number of iterations """
        for _ in range(iterations):
            self.run()

    def run(self):
        """ function that starts each"""

        # connect to Nova
        ec2_conn = boto.connect_ec2(**utils.get_rc_credentials())
       
        name =  self.random_name(20)
        test_result = "Error"
        try:
            ec2_conn.create_key_pair(name)
            ec2_conn.get_all_key_pairs(name)
            test_result = ec2_conn.delete_key_pair(name)
        except Exception:
            # pass
            utils.log("Error")

        #utils.log("%s Unexpected state in VM after run() %r" % (instance_id, instance.state))
        utils.add_record( {'key_name': name, 'test_result': test_result })     
        
if __name__ == '__main__':
    try:
        vm = keyrunner()
        vm.runner(int(sys.argv[1]), int(sys.argv[2]))
    except Exception:
        print "Usage: ./vm_runner.py number_of_workers number_of_iterations"
        print "Make sure you have sourced novarc to set env variables"
        exit(1)
    print "\n" 
    for x in utils.get_records():
        print x

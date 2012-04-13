
"""

A set of common tarkin utilities

"""

import os
import time

from boto.ec2.regioninfo import RegionInfo

start_time = time.time()

# Some sane defaults
INSTANCE_TYPE = 'm1.tiny'
REGION_NAME = 'test'


# CREDENTIALS
def get_rc_credentials():
    """generates the required values for boto.connection_ec2"""
    CREDS = set(['EC2_ACCESS_KEY', 'EC2_SECRET_KEY','EC2_URL'])
    if CREDS < set(os.environ):
        AWS_ACCESS_KEY_ID = os.environ['EC2_ACCESS_KEY']
        AWS_SECRET_ACCESS_KEY = os.environ['EC2_SECRET_KEY']
        AWS_HOST = os.environ['EC2_URL'].split('/')[2].split(':')[0]
        AWS_PORT = int(os.environ['EC2_URL'].split('/')[2].split(':')[1])
        region = RegionInfo(None, REGION_NAME, AWS_HOST)
        # is_secure=False, path='/services/Cloud' aws_access_key_id, aws_secret_access_key
        return {'aws_access_key_id': AWS_ACCESS_KEY_ID,
                'aws_secret_access_key':AWS_SECRET_ACCESS_KEY,
                'region':region,
                'port':AWS_PORT,
                'is_secure':False,
                'path':'/services/Cloud'}
    else: raise Exception("missing environment variables")


# Logging

_records = []

def add_record(testinfo):
    _records.append(testinfo)

def get_records():
    return _records

def log(msg):
    line = "[%.1f sec] %s" % (time.time() - start_time, msg)
    print line


# VM life cycle 

def checkping(instance):
    if os.system("ping -c 1 %s > /dev/null" % instance.private_ip_address) == 0:
        return True
    else:
        return False

def elapsed_time(start):
    return int(time.time() - start)

def launch_vm(self,image):
    log("Launching VM")
    reservation = image.run(instance_type=INSTANCE_TYPE)
#TODO(jogo) add key_name
#    reservation = image.run(instance_type=INSTANCE_TYPE,
#                            key_name=KEYPAIR_NAME)

    return reservation.instances[0]


def block_till_running(self, instance):
    #log("Waiting for instance %s to be in running state " % instance.id)
    result = False
    for x in range(60):
        instance.update()
        if instance.state == 'running':
            result = True
            break
        elif instance.state == 'error':
            break
        time.sleep(1)
    if result: log("%s state: running" % instance.id)
    else: log("%s state: failed to reach running" % instance.id)
    return result


def block_till_ping(self, instance, wait=300):
    #log("Waiting for instance %s to be pingable " % host)
    result = False
    for x in range(wait):
        if checkping(instance):
            result = True
            break
        time.sleep(1)
    if result: log("%s state: pingable " % instance.id)
    else: log("%s state: failed to reach ping" % instance.id)
    return result

# Other

def wait_for_tests(number_of_tests):
    """ Assumes each test writes a record when it finishes """
    while(True):    # loop until we are done with all the tests
        tests_run = len(get_records())
        log("Tests run: %d / %d " % (tests_run, number_of_tests))
        
        if tests_run == number_of_tests:
            break
        time.sleep(2)

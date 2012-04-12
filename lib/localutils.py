
"""

A set of common commands around launching and checking the state of VMs.

"""

import os
import time

start_time = time.time()

# Some sane defaults
INSTANCE_TYPE = 'm1.tiny'

_tests = []

def add_record(testinfo):
    _tests.append(testinfo)

def get_records():
    return _tests

def log(msg):
    line = "[%.1f sec] %s" % (time.time() - start_time, msg)
    print line

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
#TODO add key_name
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

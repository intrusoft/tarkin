
import os
import time

start_time = time.time()


def log(msg):
    line = "[%.1f sec] %s" % (time.time() - start_time, msg)
    print line


def checkping(host):
    if os.system("ping -c 1 %s > /dev/null" % host) == 0:
        return True
    else:
        return False


def launch_vm(self):
    log("Launching VM")
    image = self.ec2_conn.get_image(_ami)
    reservation = image.run(kernel_id=_aki,
                            ramdisk_id=_ari,
                            instance_type=INSTANCE_TYPE,
                            key_name=KEYPAIR_NAME)

    return reservation.instances[0]


def block_till_running(self, inst):
    log("Waiting for instance %s to be in running state " % inst.id)
    result = False
    for x in range(60):
        inst.update()
        if inst.state == 'running':
            result = True
            break
        time.sleep(1)
    return result


def block_till_ping(self, host, wait=60):
    #log("Waiting for instance %s to be pingable " % host)
    result = False
    for x in range(wait):
        if checkping(host):
            result = True
            break
        time.sleep(1)
    log("Instance %s is  pingable " % host)
    return result

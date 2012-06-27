#!/usr/bin/env python

import os
import sys
import re
import time

from lib.localutils import checkping
from lib.sshutils import SSHCommand


import boto
from boto.ec2.regioninfo import RegionInfo

KEY_PATH = '/root/test.pem'

# Some sane defaults
INSTANCE_TYPE = 'm1.tiny'
REGION_NAME = 'test'
KEYPAIR_NAME = 'test'

_ami = 'ami-00000001'
_aki = 'aki-00000003'
_ari = 'ari-00000002'

start_time = time.time()

def _log(msg):
    line = "%d %s" % (int(time.time() - start_time), msg) 
    print line

class SGRogue():
    def __init__(self, region, awshost, awsaccesskey, awssecretkey, awsport):
        _log("Connecting to end-point")
        self.region = RegionInfo(None, region, awshost)
        self.ec2_conn = boto.connect_ec2(awsaccesskey,awssecretkey,
                                         region=self.region, 
                                         port=awsport, 
                                         is_secure=False, 
                                         path='/services/Cloud')

        self.ssh = SSHCommand(KEY_PATH)
   
    def _launch_vm(self):
        _log("Launching VM")
        image = self.ec2_conn.get_image(_ami)
        reservation = image.run(kernel_id=_aki, 
                                ramdisk_id=_ari, 
                                instance_type=INSTANCE_TYPE, 
                                key_name=KEYPAIR_NAME)

        return reservation.instances[0]

    def _block_till_running(self, inst):
        _log("Waiting for instance %s to be in running state " % inst.id)
        result = False
        for x in range(60):
            inst.update()
            if inst.state == 'running':
                result = True
                break
            time.sleep(1)
        return result
        
    def _block_till_ping(self, host):
        _log("Waiting for instance %s to be pingable " % host)
        result = False
        for x in range(60):
            if checkping(host):
                result = True
                break
            time.sleep(1)
        return result

    def _instance_ping_out(self, ssh_host, host):
        #_log("Attempting to ping from %s to %s " % (ssh_host, host))
        buffer = self.ssh.cmdexec(ssh_host, 'ping -W 5 -q -n -c 1 %s' % host)
        if '1 received' in buffer[0]:
            return True
        else:
            return False

    def _instance_tcp_out(self, ssh_host, host, port):
        #_log("Attempting to reach %s:%d from %s " % (ssh_host, int(port), host))
        buffer = self.ssh.cmdexec(ssh_host, 'nc -v -d -v -z -w 1 %s %d ' % (host, int(port)) )
        if 'succeeded' in buffer[0]:
            return True
        else:
            return False

    def _instance_detect_vulnerable_ips(self, ssh_host):
        buffer = self.ssh.cmdexec(ssh_host, 'route -n')
        subs = re.findall(r'0.0.0.0\s+([\d]+\.[\d]+\.[\d]+\.[\d]+)\s+0.0.0.0', buffer[0])
        if subs:
            gw = subs[0]

        def find_route_hop(hop_distance):
            buffer = self.ssh.cmdexec(ssh_host, 'ping -c 1 -n -t %d 8.8.8.8' % int(hop_distance))
            subs = re.findall(r'From\s+([\d]+\.[\d]+\.[\d]+\.[\d]+)\s+icmp', buffer[0])
            if subs:
                ip = subs[0]
                return ip

        host_ip = find_route_hop(2)
        host_gw = find_route_hop(3)

        ip_list = [('gw',gw),('host_ip',host_ip),('host_gw',host_gw)]

        return ip_list


    def _instance_ssh_ready(self, ssh_host):
        _log("Waiting for SSH to be ready on %s " % ssh_host)
        result = False
        for x in range(120):
            buffer = self.ssh.cmdexec(ssh_host, 'uptime')
            if 'load average' in buffer[0]:
                result = True
                break
            time.sleep(5)
        return result
        

    def run(self):
        evil_inst = self._launch_vm()

        if not (self._block_till_running(evil_inst) ):
            _log("Error while waiting for instances to reach running state")
            return

        if not ( self._block_till_ping(evil_inst.public_dns_name) ):
            _log("Error while waiting for instances to be pingable from this host")
            return

        if not (self._instance_ssh_ready(evil_inst.public_dns_name) ):
            _log("Error while waiting for instances to be SSH'able")
            return

        _log("\n --- STARTING TESTS --- \n") 
 
        result = self._instance_ping_out(evil_inst.public_dns_name, '8.8.8.8')
        _log("evil instance %s (%s) can reach the public internet: %s" % ( 
            evil_inst.public_dns_name, evil_inst.id, result))        


        # try and hit any of the bridge interfaces on the host
        self._instance_detect_vulnerable_ips(evil_inst.public_dns_name)

        # try and hit any of the physical interfaces on the host
        vulnips = self._instance_detect_vulnerable_ips(evil_inst.public_dns_name)
        for (host,ip) in vulnips:
            print "Testing if %s(%s) is reachable via ping(ICMP) %s " % (
                  host,
                  ip,
                  self._instance_ping_out(evil_inst.public_dns_name, ip) ) 

            print "Testing if %s(%s) is reachable via SSH(TCP port 22) %s " % (
                  host,
                  ip,
                  self._instance_tcp_out(evil_inst.public_dns_name, ip, 22) )

            print "Testing if %s(%s) is reachable via SSH(TCP port 80) %s " % (
                  host,
                  ip,
                  self._instance_tcp_out(evil_inst.public_dns_name, ip, 80) )

     
if __name__ == '__main__':
    if 'EC2_ACCESS_KEY' in os.environ and 'EC2_SECRET_KEY' in os.environ:
        AWS_ACCESS_KEY_ID = os.environ['EC2_ACCESS_KEY']
        AWS_SECRET_ACCESS_KEY = os.environ['EC2_SECRET_KEY']
        AWS_HOST = os.environ['EC2_URL'].split('/')[2].split(':')[0]
        AWS_PORT = int(os.environ['EC2_URL'].split('/')[2].split(':')[1])
        sg = SGRogue(REGION_NAME, AWS_HOST, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_PORT)
        sg.run()
    else:
        print "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY not set"
        print "You can do this by sourcing novarc or setting the environment variables"
        sys.exit()


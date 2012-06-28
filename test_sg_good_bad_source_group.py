import re
import time
from lib.sgtest import SGTest

class SGGoodBadSourceGroup(SGTest):

    def main(self):

        _result_good_ping_dest = False
        _result_bad_ping_dest = False
        _result_good_ssh_dest = False
        _result_bad_ssh_dest = False

        (good_group, bad_group, dest_group) = self.create_good_bad_dest()

        # allow SSH into source groups
        self.auth_from_cidr(good_group, '0.0.0.0/0', 'tcp', '22', '22')
        self.auth_from_cidr(bad_group, '0.0.0.0/0', 'tcp', '22', '22')

        # allow ping into source groups
        self.auth_from_cidr(good_group, '0.0.0.0/0', 'icmp', '-1', '-1')
        self.auth_from_cidr(bad_group, '0.0.0.0/0', 'icmp', '-1', '-1')

        # allow ICMP/ping from good group
        self.auth_from_group(dest_group, good_group, 'icmp', '-1', '-1')

        # allow SSH from good group
        self.auth_from_group(dest_group, good_group, 'tcp', '22', '22')

        keyname = self.get_new_key_pair()
        
        # spin up VMs
        dest_instance = self.launch_instance(security_groups=[dest_group], key_name=keyname)
        bad_instance = self.launch_instance(security_groups=[bad_group], key_name=keyname)
        good_instance = self.launch_instance(security_groups=[good_group], key_name=keyname)

        # wait for VMs to come up
        if self.block_until_running(dest_instance) and \
            self.block_until_running(bad_instance) and \
            self.block_until_running(good_instance):
            print "VMs are up!"
            
        # wait for 2 VMs to ping
        if self.block_until_ping(bad_instance) and \
           self.block_until_ping(good_instance):
           print "VMs can ping!"

        time.sleep(5)
        # ping from good to dest
        output = self.ssh_cmd_simple(good_instance, keyname, 'ping -c 1 %s' % dest_instance.private_ip_address)
        print output
        if '1 receive' in "".join(output):
            _result_good_ping_dest = True

        # ping from bad to dest
        output = self.ssh_cmd_simple(bad_instance, keyname, 'ping -c 1 %s' % dest_instance.private_ip_address)
        print output
        if '0 receive' in "".join(output):
            _result_bad_ping_dest = True

        # ssh into good to dest
        output = self.ssh_cmd_simple(good_instance, keyname, 'nc -v -d -v -z -w 1 %s 22' % dest_instance.private_ip_address)
        print output
        if 'succeeded' in "".join(output):
            _result_good_ssh_dest = True
            
        # ssh from bad to dest
        output = self.ssh_cmd_simple(bad_instance, keyname, 'nc -v -d -v -z -w 1 %s 22' % dest_instance.private_ip_address)
        print output
        if 'timed out' in "".join(output):
            _result_bad_ssh_dest = True


        self.add_result(test_name=self.__class__.__name__+'_good_ping_dest', result=_result_good_ping_dest)

        self.add_result(test_name=self.__class__.__name__+'_bad_ping_dest', result=_result_bad_ping_dest)        

        self.add_result(test_name=self.__class__.__name__+'_good_ssh_dest', result=_result_good_ssh_dest)

        self.add_result(test_name=self.__class__.__name__+'_bad_ssh_dest', result=_result_bad_ssh_dest)

        # cleanup
        time.sleep(2)
        self.terminate(dest_instance)
        self.terminate(bad_instance)
        self.terminate(good_instance)


        for x in range(100):
            # for some reason it takes a long time to terminate an instance
            if self.get_instance_status(dest_instance) == 'terminated' and \
                self.get_instance_status(bad_instance) == 'terminated' and \
                self.get_instance_status(good_instance) == 'terminated':
                break
            time.sleep(1) 
   
        self.delete_group(dest_group)
        self.delete_group(bad_group)
        self.delete_group(good_group)

        self.delete_key_pair(keyname)


        """
        _result = False
        tmp_group = 'tmp_' + self.rndstr(6)
        print "create group: %s" % tmp_group
        self.create_group(tmp_group)

        instance = self.launch_instance(security_groups=[tmp_group])

        # run instance with group
        
        if self.block_until_running(instance):
            if not self.block_until_ping(instance,timeout=25):
                _result = True

        self.add_result(test_name=self.__class__.__name__, result=_result)

        self.terminate(instance)

        for x in range(20):
            if self.get_instance_status(instance) == 'terminated':
                break
            time.sleep(1)

        # can't delete group when vm is still associated with it
        self.delete_group(tmp_group)       
        """

if __name__ == '__main__':
    o = SGGoodBadSourceGroup()
    o.main()
    o.emit_results()


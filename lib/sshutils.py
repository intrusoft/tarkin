import os
import sys
import time
import paramiko
import socket


class SSHCommand():
    def __init__(self, key_path):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.key_path = key_path

    def cmdexec(self, remote_host, cmd):
        try:
            self.ssh.connect(remote_host, key_filename=self.key_path)
        except Exception, e:
            return('','','exceptions.EOFError')
        except socket.error:
            return('','','socket.error')

        so = ''
        try:
            trn = self.ssh.get_transport()
            chn = trn.open_session()
            chn.set_combine_stderr(True)
            chn.exec_command(cmd)
        except SSHException, e:
            return ('', '', str(e))

        i = 0
        while i < 10 and not chn.recv_ready():
            time.sleep(0.1)
            i += 1

        try:
            part = chn.recv(65536)
            while part:
                so += part
                part = chn.recv(65536)
        except SSHException, e:
            return ('', '', str(e))
        except socket.timeout:
            return ('', '', 'socket.timeout')

        return (so, '', '')


if __name__ == '__main__':
    if len(sys.argv) > 0:
        key_path = sys.argv[1]
    else:
        key_path = '/root/test.pem'
    
    sc = SSHCommand(key_path)
    print sc.cmdexec("10.50.0.6", "uptime")





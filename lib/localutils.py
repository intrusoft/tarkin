
import os

def checkping(host):
    if os.system("ping -c 1 %s > /dev/null" % host) == 0:
        return True
    else:
        return False





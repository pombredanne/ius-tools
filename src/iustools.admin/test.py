import pexpect
from time import sleep

_file = '/home/ius-admin/ius-repo/ius/archive/Redhat/5/i386/mysql51-bench-5.1.56-1.ius.el5.i386.rpm'
cmd = "/bin/rpm --resign %s" % _file
passphrase = "4wwTa@ow51oW"
child = pexpect.spawn(cmd)
res = child.expect('Enter pass phrase:')
res = child.sendline(passphrase)
child.wait()
print child.exitstatus

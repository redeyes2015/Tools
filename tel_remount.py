#!/usr/bin/env python
import telnetlib
import sys
import os

if len(sys.argv) < 2:
	#print "use `%s IP` to remount via telnet" % sys.argv[0]
	#exit()
	nvr_ip = "172.18.80.23"
else:
	nvr_ip = sys.argv[1]

nvr = telnetlib.Telnet(nvr_ip)

nvr.read_until('login:')

print 'connected'

nvr.write('root\n')

idx, _, _ = nvr.expect(['Password: ', '# '], 10)
if idx == 0:
	print 'need password... read from env var: NR_PASSWORD'
	nvr.write(os.environ["NR_PASSWORD"] + '\n')
	nvr.read_until('# ')

print 'logged in'

nvr.write('echo remounting /www > /dev/console\n')
nvr.write('umount /www; mount -o nolock 172.18.1.180:/export/www /www; exit\n')

print nvr.read_all()

print '... done'



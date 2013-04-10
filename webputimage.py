#!/usr/bin/env python
import sys
import os

def which(program):
	def is_exe(fpath):
		return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

	fpath, fname = os.path.split(program)
	if fpath:
		return program if is_exe(program) else None
	#else:
	for path in os.environ["PATH"].split(os.pathsep):
		path = path.strip('"')
		exe_file = os.path.join(path, program)
		if is_exe(exe_file):
			return exe_file

	return None

if which('curl') is None:
	print "You don't have curl installed!"
	sys.exit(1)

from optparse import OptionParser

optParser = OptionParser(usage="usage: %prog [options] IP [IMGPATH]")
optParser.add_option("-u", "--user", dest="username", default="admin",)
optParser.add_option("-p", "--password", "--passwd", dest="passwd", default="admin",)
optParser.add_option("-b", "--base64", action="store_true", dest="usebase64", default=False,
		help='Using base64 encode to login')
optParser.add_option("-n", "--nopad", action="store_true", dest="nopad", default=False,
		help='Not using random(?) padding to login')
optParser.add_option("-d", "--debug", action="store_true", dest="debug", default=False,
		help='Test whether we could login')

(options, args) = optParser.parse_args()

if len(args) < 1:
	optParser.error("incorrect number of arguments")

ip = args[0]
img_path = args[1] if len(args) > 1 else "images/firmware.img"

if not options.debug:
	if not os.path.isfile(img_path):
		optParser.error("%s not found!" % img_path)

	if os.path.getsize(img_path) == 0:
		optParser.error("%s has zero size!?" % img_path)

import base64
from subprocess import Popen,PIPE,STDOUT

def gen_nr_pem(system_key):
	import json
	from binascii import unhexlify
	hex_pub = json.loads(system_key)['n']
	key_len = -1

	if len(hex_pub) == 128: #512bits
		hex_der = ('305c300d06092a864886f70d010101050003' +
			'4b003048024100' + hex_pub + '0203010001')
		key_len = 512
	elif len(hex_pub) == 256: #1024bits
		hex_der = ('30819f300d06092a864886f70d010101' +
				'050003818d0030818902818100' + hex_pub + '0203010001')
		key_len = 1024
	else:
		print "unsupported public key length!", hex_pub
		sys.exit(1)

	b64_der = base64.b64encode(unhexlify(hex_der));

	ret = ["-----BEGIN PUBLIC KEY-----"]

	for i in range(0, len(b64_der), 64):
		 ret.append(b64_der[i:i+64])
	ret.append("-----END PUBLIC KEY-----")

	return key_len, "\n".join(ret)

def get_encode(options, ip):
	encode = ""
	if options.usebase64:
		return base64.b64encode("%s:%s" % (options.username, options.passwd))
	#else:
	import tempfile

	proc = Popen(['curl', '-s', "http://%s/fcgi-bin/system.key" % ip], stdout=PIPE)
	key_len, pub_pem = gen_nr_pem(proc.communicate()[0])

	(key_fd, key_f_path) = tempfile.mkstemp()
	key_f = os.fdopen(key_fd, "w")
	key_f.write(pub_pem)
	key_f.flush()
	key_f.close()

	def get_cipher(text):
		from binascii import hexlify
		proc = Popen(['openssl', 'rsautl', '-encrypt', '-inkey', key_f_path, '-pubin'],
				stdin=PIPE, stdout=PIPE)
		bin_cipher = proc.communicate(text)[0]
		return hexlify(bin_cipher)

	if options.nopad:
		return get_cipher("%s:%s" % (options.username, options.passwd))
	#else:

	if key_len == 512:
		text_list = ["f000b222", "de12ad34be56ef"]
	else: #1024
		text_list = ["de12ad34be56ef"]

	text_list.append("f00ba3:%s:%s" % (options.username, options.passwd))
	return "".join(map(get_cipher, text_list))

encode = get_encode(options, ip)

def get_cookie(encode, ip):
	proc = Popen(['curl', '-s', '-D', '-', '--cookie', '/dev/null',
		'-d', "encode=%s&mode=liveview" % encode,
		 "http://%s/fcgi-bin/system.login" % ip, '-o', '/dev/null'],
		 stdout=PIPE)
	headers = proc.communicate()[0]
	cookies = []
	for l in headers.splitlines():
		if 'Set-Cookie' not in l:
			continue
		cookies.append(l.split(" ")[1].strip())
	return "".join(cookies)

cookies = get_cookie(encode, ip)

if options.debug:
	proc = Popen(['curl', '-s', '--cookie', cookies,
		'-d', 'path=/system/software/meteor/encoder',
		"http://%s/fcgi-bin/dbusproxy.gconf_query" % ip],
		 stdout=PIPE)
	cam_info = proc.communicate()[0]
	if len(cam_info) == 0:
		print 'login failed...'
		sys.exit(1)
	#else:
	print 'login success!'
	sys.exit(0)

upload_cmd = ["curl", "--cookie", cookies, "-F",
	"send_file=@%s" % img_path,
	"http://%s/fcgi-bin/system.upgrade" % ip]

if not sys.stdout.isatty():
	upload_cmd.insert(1, "-s")

print "uploading..."
proc = Popen(upload_cmd, stdout=open('/dev/null'))

proc.wait()

if proc.returncode != 0:
	print "upload failed...!?"


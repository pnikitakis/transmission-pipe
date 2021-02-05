import client as snd

ip = input("Give server's ip--")
port = input("Give server's port--")
buflen = input('Give length for buffer in positions--')
buf = input('Give file name you want to transfer--')

fd = snd.netpipe_snd_open(ip, port, buflen)

while True:
	length = input('Give the length you want to read: --')
	length = int(length)

	ret = snd.netpipe_write(fd, buf, length)
	if ret == 0:
		print("=====End of file!======")
		break

snd.netpipe_snd_close(fd)
print("this is the end from client")
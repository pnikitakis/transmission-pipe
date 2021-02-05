import server as rcv 

print("We are the server...")

port = input("Give port number. {For port = 0, OS will assign the port} --")
buflen = input('Give length for buffer in positions--')

fd = rcv.netpipe_rcv_open(port, buflen)

ret=1
while ret == 1:
	length = input('Give the length you want to read: --')
	length = int(length)
	ret = rcv.netpipe_read(fd," ", length)
	
rcv.netpipe_rcv_close(fd)

print("-----------------------------------this is the end from server-------------------------------------")


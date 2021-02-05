import statistics as s
import server as rcv
import client as snd

statsFor = "server" # or: statsFor = "server" 
ipServer = '192.168.1.106'
port = 5000
buflen = 50
buf = 'upload_test.txt'
lenRead = 512
n = 10 #100, 1000

ret1 = 1
ret2 = 1
for i in range (0, 10):
	fd = rcv.netpipe_rcv_open(port, buflen)
	fd2 = snd.netpipe_snd_open(ipServer, port, buflen)
	for j in range (0, n):
		ret2 = snd.netpipe_write(fd2, buf, lenRead)
		print('NOW IS NEXT')
		ret1 = rcv.netpipe_read(fd, ' ', lenRead)
		
	snd.netpipe_snd_close(fd2)
	rcv.netpipe_rcv_close(fd)

if statsFor == "server":

	with open('statistics_files/statsBufSpace.txt') as f:
		presentances = f.readlines()
	# remove whitespace characters `\n` at the end of each line
	presentances = [x.strip() for x in presentances] 
	presentances = list(map(float, presentances))

	meanBufSpace = s.mean(presentances)
	print('Buffer space loss, Mean: ', '%.2f' %(meanBufSpace*100), '%')
	stdvBufSpace = s.stdev(presentances)
	print('Buffer space loss, Standar Deviation: ', '%.2f' %(stdvBufSpace*100), '%')

	with open('statistics_files/statsDouble.txt') as f:
		presentances = f.readlines()
	# remove whitespace characters `\n` at the end of each line
	presentances = [x.strip() for x in presentances] 
	presentances = list(map(float, presentances))

	meanDouble = s.mean(presentances)
	print('Doubled packets loss, Mean: ', '%.2f' %(meanDouble*100), '%')
	stdvDouble = s.stdev(presentances)
	print('Doubled packets loss, Standar Deviation: ', '%.2f' % (stdvDouble*100), '%')

	meanTotal = s.mean([meanBufSpace, meanDouble])
	stdvTotal  = s.stdev([stdvBufSpace, stdvDouble])
	print('Total packets loss, mean: ', '%.2f' % (meanTotal*100) + '%')
	print('Total packets loss, standar Deviation: ','%.2f' %( stdvTotal*100), '%')

#-------
#statsSender
else:
	with open('statistics_files/statsSender.txt') as f:
		presentances = f.readlines()
	# remove whitespace characters `\n` at the end of each line
	presentances = [x.strip() for x in presentances] 
	presentances = list(map(float, presentances))

	meanFlowCtrl = s.mean(presentances)
	print('Flow control loss, Mean: ', '%.2f' %(meanFlowCtrl*100), '%')
	stdvFlowCtrl = s.stdev(presentances)
	print('Flow control loss, Standar Deviation: ', '%.2f' % (FlowCtrl*100), '%')



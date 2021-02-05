#ce323 - 1h ergasia (hmeromhnia paradoshs: 10/3/2018
#Nikitakis Panagioths (1717) - Rantou Kalliopi(2004)
#Bibliothiki tou client

import socket
import time
import threading
import struct
import sys
import os

socketsArray = []		#pinakas sockets
fds = []			#pinakas fds sockets
buffers = []                    #2D array with buffers
buffers_size = []	        #pinakas me to buffer_size kathe sundeshs
threadsArray = []	        #pinakas apo threads
dict_files = {}		        #dictionary gia kathe file pou anoigetai me value to posa bytes exoyn diabastei 
threadId = 0                    #increase for every thread
new_id = 0			#id kathe paketou

flagFlush = False
flagClose = False

condition = threading.Condition() 
conditionFlush = threading.Condition() 

#statistika
total_times_stopped = 0
total_packets_sent = 0


#Dhmiourgia kalshs thread
class newThread(threading.Thread):
	def __init__(self, threadID, ipaddr, port, index):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.ipaddr = ipaddr
		self.port = port
		self.index = index
		self._stopevent = threading.Event()
	def run(self):
		sender_thread(self.ipaddr, self.port, self.index)


#Sunarthsh tou thread pou stelnei ta paketa panw apo thn Udo sundesh
def sender_thread(ipaddr, port, index):
	global socketsArray
	global buffers
	global flagFlush
	global flagClose
	global total_times_stopped
	global total_packets_sent
	
	port = int(port)
	index = int(index)
	
	indexPacket = 0
	s = socketsArray[index]
	
	while True:
		if flagClose == True:
			return
		
		s.settimeout(2)				#dynamika 
		
		condition.acquire()
		if len(buffers[index]) != 0:
			if (indexPacket + 1 <= len(buffers[index])):
				packet = buffers[index][indexPacket]
				indexPacket = indexPacket + 1
				print("Sending packet to server.")
				s.sendto(packet, (ipaddr, port))	
				total_packets_sent += 1 #statistika
		condition.release()
		
		start = time.time()
		
		try:
			data, addr = s.recvfrom(1024)
			print("Received data from server:", data)
			
			data = data.decode("utf-8")
			
			if data[0] == 'N':   		# [N]ack
				temp,packetID = data.split(",")
				packetID = int(packetID)
				
				print("nackID: " , packetID)
			elif data[0] == 'M': 		# [M]issing
				temp,packetID = data.split(",")
				packetID = int(packetID)
				print("Missing Id: " , packetID)
				
				condition.acquire() 	#get lock
				for elem in buffers[index]:
					tempPos = elem.find(b',')
					elemID = elem[0:tempPos].decode("utf-8")
					elemID = int(elemID)

					if elemID == packetID:
						s.sendto(elem, (ipaddr, port))
						packetID -= 1
						break
				condition.release()
			elif data[0] == 'F': # [F]low
				temp,packetID = data.split(",")
				packetID = int(packetID)
				#do smthing with flow
				
			total_times_stopped += 1 #statistika
			
			condition.acquire()
			for elem in buffers[index]:
				tempPos = elem.find(b',')
				elemID = elem[0:tempPos].decode("utf-8")
				elemID = int(elemID)
				
				if elemID == packetID:
					indexToDelete = buffers[index].index(elem)
					del buffers[index][:indexToDelete + 1]
					
					print("Delete packets from client's buffer.")
					indexPacket = indexPacket - indexToDelete - 1
					condition.notify()
					break
				elif elemID > packetID:
					break
			condition.release()
			
			elapsed = (time.time()-start)
			
		except socket.timeout:
			pass
		
		#se periptwsh pou o buffer ftasei sto 80% ths  xwrhtikothtas tou stelnei mhnyma gia diagrafh paketwn
		condition.acquire()
		if len(buffers[index]) != 0:
			if len(buffers[index])/buffers_size[index] >= 0.8 or flagFlush == True:
				firstIdPos = buffers[index][0].find(b',')
				firstId = buffers[index][0][:firstIdPos].decode("utf-8")
				
				message = "From client: Need nack!" +  firstId
				s.sendto(bytes(message, "utf-8"), (ipaddr, port))
				total_times_stopped += 1 #statistika
		condition.release()
		
		#otan o pinakas einai adeios kai to flagFlush == true eidopoieitai h netpipe_flush gia na termatisei
		conditionFlush.acquire()
		if flagFlush == True and len(buffers[index]) == 0:
			conditionFlush.notify()
		conditionFlush.release()

	return


#Sunarthsh gia th dhmiourgia sundeshs me to sugkekrimeno ip kai port
def netpipe_snd_open(ipaddr, port, bufsize):
	global socketsArray
	global fds
	global buffers_size
	global buffers
	global threadId
	global threadsArray
	
	port = int(port)
	bufsize = int(bufsize)
	
	bufA = []
	
	udp_ipB = ipaddr
	udp_portB = port
    
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  	#create UDP connection
	
	#arxikopoihsh pinakwn
	socketsArray.append(s)
	fds.append(s.fileno())
	buffers.append(bufA)
	buffers_size.append(bufsize)
	
	s.settimeout(0.5)
	
	for i in range (0,5):
		message = "Are you open?"								#elegxos gia to an einai anoixto to akro anagnwshs
		start = time.time()
		s.sendto(bytes(message, "utf-8"), (udp_ipB, udp_portB))
		try:
			data, addr = s.recvfrom(1024)
			elapsed = (time.time() - start)
			print("Received message from server:", data)
			break
		except socket.timeout:
			print("Timeout!!! Try again...")
			
	time.sleep(2)
	if i == 4:													#an perasei to xroniko perithwrio h sundesh kleinei
		print("Timeout. Close connection!")
		return -1
	else:
		threadId = threadId + 1
		th1 = newThread(threadId, udp_ipB, udp_portB, (len(buffers)-1))
		threadsArray.append(th1)
		th1.start()
		
		return fds[-1]

#sunarthsh gia to grapsimo dedomenwn apo to dosmeno arxeio ston buffer tou client
#ta dedomena ginontai paketa me sugkekrimeno id kai arithmo bytes
def netpipe_write(fd, buf, length):
	global new_id
	global buffers
	global buffers_size
	global fds
	global dict_files
	
	fd = int(fd)
	length = int(length)
	filename = buf
	flagEOF = False
	
	if filename in dict_files:
		pass
	else:
		print("Open for the first time the file:", filename)
		dict_files[filename] = 0			#an to filename den uparxei hdh mesa sto dictionary tote arxikopieitai
											#h antisoixh thesh me 0, osa dhladh kai ta bytes pou exoun diavastei mexri twra
	
	pos = fds.index(fd)
	file_size = os.stat(filename)
	
	f = open(filename, "rb")
	f.seek(dict_files[buf], 0)			#metakinhsh deikth panw sto arxeio, toswn thesewn osa kai ta bytes pou exoun hdh diavastei
	
	data_sent = 0				#metrhths gia ta bytes pou exoun perastei ston buffer
	
	while data_sent < length and flagEOF == False:	#oso einai ligotera apo to length pou zhththike
		bytes_remaining = (file_size.st_size) - dict_files[buf]		#arithmos bytes pou perisseuoun sunolika
		print("Bytes remaining for reading from file: ", bytes_remaining)
		
		if(new_id == 0):	#an einai to prwto paketo, tha exei san dedomeno kai to filename
			filename += ','
			packet = (str(new_id) + ','  +  filename).encode("utf-8")
		else:
			packet = (str(new_id) + ',').encode("utf-8")
		
		packetSize = sys.getsizeof(packet)
		print("Packet size in client's buffer: ", packetSize)
		
		if bytes_remaining <= 0:		
			print("End of file. No more bytes for reading!") 
			
			data = bytes('--EOF--', 'utf-8')
			flagEOF = True
		elif (length <= 1024 - packetSize):		#an to length einai mikrotero apo to megethos tou paketou
			if length - bytes_remaining > 0:	#alla perissotera apo ta bytes pou perisseuoun tote diabazoume ayta ta bytes
				data = f.read(bytes_remaining)
				dict_files[buf] = dict_files[buf] + bytes_remaining
			else:								#diaforetika diabazoume tosa bytes osa zhththikan
				data = f.read(length)
				dict_files[buf] = dict_files[buf] + length			
		elif (length >= 1024 - packetSize):		#an to length einai megalytero apo o megethos tou paketou, tote
			if (1024 - packetSize) - bytes_remaining > 0:	#an to paketo einai megalytero apo ta bytes pou perisseuoun diabazoume 
				data = f.read(bytes_remaining)				#tosa bytes
				dict_files[buf] = dict_files[buf] + bytes_remaining
			else:											#diaforetika pairnoume olo to paketo
				data = f.read(1024 - packetSize)
				dict_files[buf] = dict_files[buf] + (1024 - packetSize)
			
		packet += data			#apothikeysh data sto paketo
		
		condition.acquire()
		print("new_id: ", new_id)
		print("packet size total", sys.getsizeof(packet))
		print("buffer length: ", len(buffers[pos]))
		print("buffers_size: ",  buffers_size[pos])
		print('-----')
		
		
		while len(buffers[pos]) >= buffers_size[pos]:
			print("Clinet's buffer is full!")
			condition.wait()
			print("List emptied one slot. Begin!")
		buffers[pos].append(packet)
		
		condition.release()
		
		new_id = new_id + 1
		data_sent += sys.getsizeof(data)
    
	f.close()
	
	if flagEOF:
		return 0
	else:
		return 1

#sunarthsh h opoia mplokarei mexri na staloun kai epibebaiwthoun ola ta paketa pou uparxoun ston buffer
def  netpipe_flush(fd):
	global flagFlush
	fd = int(fd)
	
	conditionFlush.acquire()
	flagFlush = True
	conditionFlush.wait()
	flagFlush = False
	conditionFlush.release()
	
	return 1

#Sunarthsh gia to kleisimo olwn twn sundesewn kai th diagrafh twn pinakwn
def netpipe_snd_close(fd):
	global fds
	global socketsArray
	global buffers
	global buffers_size
	global flagClose
	global threadsArray
	fd = int(fd)
	index = fds.index(fd)
	
	ret = netpipe_flush(fd)
	
	print("Times stopped for 'logistics'", total_times_stopped)
	print("Total packets sent", total_packets_sent)
	
	stopped_presentance = total_times_stopped / (total_packets_sent + total_times_stopped)
	
	flagClose = True
	time.sleep(5) #gia bebaiwsh pws teleiwse to sender thread 
	
	os.makedirs(os.path.dirname('statistics_files/'), exist_ok=True)
	with open('statistics_files/statsSender.txt', 'a') as f:
		f.write(str(stopped_presentance)+'\n')
	
	if ret == 1:
		del fds[index]
		del socketsArray[index]
		del buffers[index]
		del buffers_size[index]
		del threadsArray[index]
		
		return 0
	else:
		return 1

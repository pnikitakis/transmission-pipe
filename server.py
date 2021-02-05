import socket
import time
import threading
import struct
import sys
import os

socketsArray = []		#pinakas sockets
fds = []				#pinakas fds sockets
buffers = []       	 	#2D array with buffers
buffers_size = []		#pinakas me to buffer_size kathe sundeshs
threadsArray = []  		#pinakasapo threads
filenameArray = []		#pinakas opou apothikeuotai ta filenames

threadId = 0
lastPacketIndex = -1

flagFilename = False
flagClose = False
flagNack = False

condition = threading.Condition() 

#gia statistika
total_packets_lost_double = 0
total_packets_lost_buf_space = 0
total_packets_arrived = 0

class newThread(threading.Thread):
	def __init__(self, threadID, index):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.index = index
	def run(self):
		receiver_thread(self.index)

def receiver_thread(index):
	global socketsArray
	global fds
	global buffers_size
	global buffers
	global threadId
	global lastPacketIndex
	global filenameArray
	global flagFilename
	global flagClose
	global flagNack
	global total_packets_lost_double
	global total_packets_lost_buf_space
	global total_packets_arrived
	
	index = int(index)
	
	s = socketsArray[index]
	message = ""
	lastPacketID = -1
	lastPacketIndex = -1
	
	while message != b'Are you open?':
		message, address = s.recvfrom(1024)
		print("Client is probably trying to connect: ", message)
	
	for i in range (0,3):
		s.sendto(b"SERVER OK", address) 
		time.sleep(0.5)
		
	while True:
		s.settimeout(2)
		
		if flagClose == True:		#flag pou eidopoiei gia to kleisimo tou sugkekrimenou thread
			return
		
		try:
			message, address = s.recvfrom(1024)
			
			checkEof = message.find(b'--EOF--')		#elegxos kathe fora tou message apo ton client gia Eof 
			tempPosFir = message.find(b',')
		
			if checkEof != -1:		#EOF
				packetID = message[0:checkEof-1].decode("utf-8")
				packetID = int(packetID)
				packet = message[checkEof:]
				
				mesEnd = "N,"+ str(packetID)	#o server stelnei paketo 
				for i in range(0,3):
					s.sendto(bytes(mesEnd, "utf-8"), address)
			elif tempPosFir == -1:
				flagNack = True
			else:
				packetID = message[0:tempPosFir].decode("utf-8")
				packetID = int(packetID)
				
				if(packetID == 0):
					tempPosSec = message.find(b',', 2)
					packetFilename = message[tempPosFir+1:tempPosSec].decode("utf-8")
					filenameArray.append(packetFilename)
					flagFilename = True
					
					packet = message[tempPosSec+1:]
				else:
					packet = message[tempPosFir+1:]


			if flagNack == True:								#if message == "From client: Need nack!":
				tempPos = message.find(b'!')
				
				tempId = message[tempPos+1:]
				tempId = tempId.decode("utf-8")
				tempId = int(tempId)
				
				condition.acquire()
				if tempId <= lastPacketID:
					if len(buffers[index]) != 0:
						for elem in buffers[index]:
							if elem is None:
								lastValidIdIndex = buffers[index].index(elem) - 1
								lastValidID = lastPacketID - (lastPacketIndex - lastValidIdIndex) 
							else:
								lastValidID = lastPacketID
							nackPacket = 'N,' + str(lastValidID)
							s.sendto(bytes(nackPacket, "utf-8"), address)
				condition.release()
			else:
				print("packetID: ", packetID)
				print("lastPacketID: ", lastPacketID)
				print("lastPacketIndex: ", lastPacketIndex)
				
				condition.acquire() #synchronize
				
				if packetID < (lastPacketID - lastPacketIndex): #Id mikrotero apo to 1o paketo toy buffer
					print('1 --- petama')
					total_packets_lost_double += 1
				elif packetID <= lastPacketID: 					#id endiameso paketo ston buffer
					relativePos = lastPacketID - packetID
					pos = lastPacketIndex - relativePos
					
					if buffers[index][pos] is None: #ean uparxei hdh uparxon paketo sth thesi toy
						buffers[index][pos] = packet
						
						total_packets_arrived += 1 #statistika
					else:
						print('2 --- petama')
						total_packets_lost_double += 1 #statistika
				else: 											#id megalutero apo to teleutaio stoixeio tou buffer
					relativePos = packetID - lastPacketID 
					pos = lastPacketIndex + relativePos
					
					if pos >= buffers_size[index]:				 #den uparxei adeia thesi
						print('3 --- petama')
						total_packets_lost_buf_space += 1 #statistika
						
						for i in range (lastPacketIndex+1, buffers_size[index]):	 #gemise None tis endiameses theseis
							buffers[index].append(None)
							lastPacketID +=1
							lastPacketIndex += 1
						
					else:
						for i in range (lastPacketIndex+1, pos):	 #gemise None tis endiameses theseis
							buffers[index].append(None)
							
						buffers[index].append(packet)				#update buffer + mtavlites
						total_packets_arrived += 1 #statistika
						lastPacketID = packetID
						lastPacketIndex = pos 
				
				condition.notify() # we have a new packet
				condition.release()
			#eddw stop to try tou recv?
		except socket.timeout:
			pass
			
			
		condition.acquire()
		#take first packet that missing
		nackPos = -1
		if len(buffers[index]) != 0:
			for x in buffers[index]:
				if x is None:
					nackPos = buffers[index].index(x)
					missingID = lastPacketID - nackPos
					msg = ('M,' + str(missingID)).encode("utf-8")
					s.sendto(msg, address)
					break
		
		#print("--------------------------------------------", buffers[index])
		flagNack = False
		condition.release()
		
	return


def netpipe_rcv_open(port, bufsize):
	global socketsArray
	global fds
	global buffers_size
	global buffers
	global threadId
	global threadsArray
	
	port=int(port)
	buffer_size = int(bufsize)
	bufB = []
	
	tmp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	tmp.connect(("8.8.8.8", 80))
	ipB =  tmp.getsockname()[0]   
	tmp.close()
	
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind((ipB, port))
	port = s.getsockname()[1]
	
	print("SERVER IP: " + ipB + " Port: " , port)
	
	socketsArray.append(s)
	fds.append(s.fileno())
	buffers.append(bufB)
	buffers_size.append(bufsize)
	
	
	threadId = threadId + 1
	th1 = newThread(threadId, (len(buffers)-1))
	threadsArray.append(th1)
	th1.start()
	
	
	return fds[-1]


def netpipe_read(fd, buf, length):
	global new_id
	global buffers
	global buffers_size
	global fds
	global dict_files
	global filenameArray
	global lastPacketIndex
	global flagFilename
	
	length = int(length)
	fd = int(fd)
	filename = buf
	
	index = fds.index(fd)
	
	if filename == ' ':
		while flagFilename == False:
			time.sleep(1)
		filename = filenameArray[index]
		
	os.makedirs(os.path.dirname('recieved_files/'), exist_ok=True)
	filename = 'recieved_files/' + filename
	
	f = open(filename, "ab")
	
	bytesToRead = length
	flagEoF = False
	condition.acquire()
		
	while True:
		print(buffers[index]) 
		
		if len(buffers[index]) == 0:
			if bytesToRead == 0:
				break
			condition.wait()
		elif buffers[index][0] is None:
			if bytesToRead == 0:
				break
			condition.wait()
		elif len(buffers[index][0]) <= bytesToRead:
			if buffers[index][0] == b'--EOF--':
				flagEoF = True
				break
			
			bytesToRead -= len(buffers[index][0])
			data = buffers[index].pop(0)

			f.write(data)
			lastPacketIndex = lastPacketIndex - 1
		elif bytesToRead > 0:
			if buffers[index][0] == b'--EOF--':
				flagEoF = True
				break
			data = buffers[index][0][:bytesToRead]
			buffers[index][0] = buffers[index][0][bytesToRead:]
			bytesToRead = 0
			f.write(data)
		else: #bytesToRead = 0
			break
		
	condition.release()
	
	f.close()
	
	if flagEoF == True:
		del buffers[index][0]
		return 0
	else:
		return 1


def netpipe_rcv_close(f):
	global fds
	global socketsArray
	global buffers
	global buffers_size
	global flagClose
	global threadsArray
	global filenameArray
	global total_packets_lost_buf_space
	global total_packets_lost_double
	global total_packets_arrived
	
	index = fds.index(fd)
	
	
	#statistika
	print('Lost packets because of buffer space', total_packets_lost_buf_space)
	print('Lost packets because of doubles:', total_packets_lost_double)
	print('Total packets arrived normally:', total_packets_arrived)
	
	
	lost_pres_space = total_packets_lost_buf_space  / (total_packets_arrived + total_packets_lost_buf_space + total_packets_lost_double)
	lost_pres_double = total_packets_lost_double / (total_packets_arrived + total_packets_lost_buf_space + total_packets_lost_double)
	
	flagClose = True
	time.sleep(5) #gia na eimaste sigouroi pws 8a termatisei to rcv_thread
	
	os.makedirs(os.path.dirname('statistics_files/'), exist_ok=True)
	
	with open('statistics_files/statsBufSpace.txt', 'a') as f:
		f.write(str(lost_pres_space)+'\n')
	with open('statistics_files/statsDouble.txt', 'a') as f:
		f.write(str(lost_pres_double)+'\n')
	
	if ret == 1:
		del fds[index]
		del socketsArray[index]
		del buffers_size[index]
		del buffers[index]
		del threadsArray[index]
		del filenameArray[index]
		
		return 0
	else:
		return 1
	


import sys
import socket
import threading
import time
from time import sleep
import keyboard
import os
sys.setrecursionlimit(10**8)

host = "localhost"
port = 8078

flag_connected = 0
flag_quit = 0
client = None

condition = [False]*4
is_space_pressed = False

d = {
        "waist_pitch": 0, "waist_yaw": 1, "left_arm_pitch": 2,
        "left_arm_roll": 3, "right_arm_pitch": 4, "right_arm_roll": 5,
        "head_pitch": 6, "head_roll": 7, "head_yaw": 8,
        "eye_pitch": 9, "left_eye": 10, "right_eye": 11,
        "eyelid": 12, "mouth": 13
    }

def supervised_sleep(duration, function):
	num = int(duration * 100)
	for _ in range(num):
		function()
		sleep(0.009)

def key_func():
	global is_space_pressed
	# quit the program
	if keyboard.is_pressed('esc'): 
		init_pos()
		print("Terminating CommU")
		os._exit(-1)
	# trigger the keyboard function
	elif keyboard.is_pressed("space"):
		if not is_space_pressed:
			is_space_pressed = True
			print("Space detected")
			look_at_you()
			supervised_sleep(3, key_func)
			init_pos()   
			for i in range(4):
				if condition[i]:
					is_space_pressed = False
					eval("condition{}()".format(i))
			

def send(data):
  global client
  global flag_connected
  if flag_connected > 0:
    senddata = bytes(data, 'sjis')
    try:
      client.sendall(senddata)
    except ConnectionResetError:
      print("ConnectionResetError")

def connect2socket():
  global flag_quit
  global flag_connected
  global client
  global lastmsg
  global host
  global port

  while flag_quit == 0:
    sockerror = -1
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    print('trying connection <',host,',',port,'>')
    while sockerror != 0 and flag_quit == 0:
      sockerror = client.connect_ex((host, port)) 
      if sockerror == 0:
        #print (client)
        flag_connected = 1
        print('connected to <',host,',',port,'>')
      else:
        flag_connected = 0

    if flag_quit == 1:
      flag_connected = 0
      print('quit socket')
      break

    client.settimeout(1) # None -> 1 second
    #client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, 1) # does not work properly
    while flag_quit == 0 and flag_connected > 0:
      try:
        rcvmsg = client.recv(1024)
        #msg = rcvmsg.decode()
        if len(rcvmsg) == 0:
          flag_connected = 0
          print ('disconnected (len(rcvmsg) == 0) from <',host,',',port,'>')
          break
      except (ConnectionAbortedError, ConnectionResetError) as e:
        flag_connected = 0
        print ('disconnected (error) from <',host,',',port,'>', e)
        time.sleep(2)
        pass
      except (OSError) as e:
        #print (e)
        pass

    client.close()
    print('socket quit')

def move(joint_name, val, sleep_time=.1):
	priority=3
	velocity=1000
	keeptime = 300
	command = '/movemulti5 {} {} {} {} {} \n'.format(d[joint_name], val, velocity, priority, keeptime*1000)
	send(command)
	supervised_sleep(sleep_time, key_func)


def move5(joint_name, val, duration=1, priority=4, keeptime=300, sleep_time=1):
	
	command = '/movemulti5 {} {} {} {} {} \n'.format(d[joint_name], val, duration*1000, priority, keeptime*1000)
	# print(joint_name)
	send(command)
	time.sleep(sleep_time)



def init_pos():
	print("Now initializing.")
	for key in d.keys():
		if key == "left_arm_pitch":
			move5(key, 90, sleep_time=.01)
		elif key == "right_arm_pitch":
			move5(key, -90, sleep_time=.01)
		else:
			move5(key, 0, sleep_time=.01)

	supervised_sleep(1, key_func)
	print("Initialized")


def look_at_you():
	print("look at you")
	move("eye_pitch", 4, .1)
	move("left_eye", -7, .1)
	move("right_eye", 10, .1)
	move("head_pitch", 0, .1)
	move("head_roll", 0, .1)
	move("head_yaw", -5, .1)
	move("waist_yaw", 30, .1)

 
def reading(duration=3):
	move("head_pitch", -10, .1)
	move("head_yaw", 0, .1)
	move("eye_pitch", -3, .1)
	move("head_roll", 0, .1)
	supervised_sleep(.1, key_func)
	
	st = time.time()
	while True:
		if time.time() - st > duration:
			return 0
		move("right_eye", 50, .1)
		move("left_eye", 60, 1)
		move("right_eye", -40, .1) 
		move("left_eye", -50, 1)  

## condition1
# 8.826 sec / loop
# left_eye, right_eye under consideration
def exploring_left():
    move("eye_pitch", 18, .1)
    move("left_eye", -25, .1)
    move("right_eye", -3, .1)
    move("head_pitch", 18, .1)
    move("head_roll", -6, .1)

    move("head_yaw", 15, .1)
    move("waist_yaw", 15, .1)
    

def exploring_right():
    move("eye_pitch", 18, .1)
    move("left_eye", -7, .1)
    move("right_eye", 25, .1)
    move("head_pitch", 18, .1)
    move("head_roll", 6, .1)
    
    move("head_yaw", -15, .1)
    move("waist_yaw", -15, .1)

def condition1():
	global condition
	condition = [False]*4
	condition[1] = True
	print("Condition 1")
	
	for _ in range(4):
		move("right_eye", 0, .1)
		move("left_eye", 0, .1)
		reading(10)
		# st = time()
	for _ in range(3):
		exploring_left()
		supervised_sleep(3, key_func)
		exploring_right()
		supervised_sleep(3, key_func)
        
		# cur = time()-st
		# with open("C:/Users/kumadalab/Desktop/COMMU/Shiro/duration_cond1.txt", "a") as f:
		#      f.write(str(cur) + "\n")

	init_pos()


## condition2
# 7.97 sec/ loop
# fixed 8.82 sec/loop
def communicative_left():
    move("eye_pitch", 0, .1)
    move("left_eye", -50, .1)
    move("right_eye", -50, .1)
    move("head_pitch", 8, .1)
    move("head_yaw", 23, .1)
    move("waist_yaw", 7, .1)

def communicative_right():
    move("eye_pitch", 0, .1)
    move("left_eye", 50, .1)
    move("right_eye", 50, .1)
    move("head_pitch", 8, .1)
    move("head_yaw", -23, .1)
    move("waist_yaw", -7, .1)

def condition2():
	global condition
	condition = [False]*4
	condition[2] = True
	print("Condition2")

	for _ in range(4):
		move("right_eye", 0, .1)
		move("left_eye", 0, .1)
		reading(10)
		# st = time()
		for _ in range(3):
			communicative_left()
			supervised_sleep(3.445, key_func)
			communicative_right()
			supervised_sleep(3.445, key_func)

        # cur = time()-st
        # with open("C:/Users/kumadalab/Desktop/COMMU/Shiro/duration_cond2.txt", "a") as f:
        #      f.write(str(cur) + "\n")
		init_pos()


## condition3
# 1.74sec?
def working_left():
    move("head_pitch", -15, .1)
    move("head_yaw", 0, .1)
    move("eye_pitch", -3, .1)
    move("head_roll", 0, .1)
    move("head_yaw", 40, .1)
    move("waist_yaw", 0, .1)

def working_right():
    move("head_pitch", -15, .1)
    move("head_yaw", 0, .1)
    move("eye_pitch", -3, .1)
    move("head_roll", 0, .1)
    move("head_yaw", -40, .1)
    move("waist_yaw", 0, .1) 

def condition3():
	global condition
	print("Condition3")
	condition = [False]*4
	condition[3] = True

	for _ in range(4):
		move("right_eye", 0, .1)
		move("left_eye", 0, .1)
		reading(10)
		# st = time()
		for i in range(10):
			working_left()
			supervised_sleep(0.5, key_func)
			working_right()
			supervised_sleep(0.5, key_func)

		# cur = time()-st
		# with open("C:/Users/kumadalab/Desktop/COMMU/Shiro/duration_cond3.txt", "a") as f:
		#      f.write(str(cur) + "\n")
	init_pos()
    
if __name__ == '__main__':
	t1 = threading.Thread(target=connect2socket)
	#t1.setDaemon (True)
	t1.start()

	time.sleep(2)
	print('send motion commands')

	while flag_quit == 0:
		if flag_connected == 1:
			init_pos()
			condition1()

		flag_quit = 1

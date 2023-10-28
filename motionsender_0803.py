import sys
import socket
import threading
import time
from time import sleep
import keyboard
import os
import winsound
import random
import sounddevice as sd
from scipy.io.wavfile import write
import cv2
import datetime as dt
import numpy as np
sys.setrecursionlimit(10**8)


#----------------------------- GLOBAL VARIABLES START -----------------------------#
host = "localhost"
port = 8078

flag_connected = 0
flag_quit = 0
client = None

condition = [False]*4
is_space_pressed = False
is_q_pressed = False
beep_on = False

# button press time recording
trl_dur = None
trl_st = None

# trial number across three conditions
# ExpNum = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 0, 1, 2, 3, 4, 5, 6, 7, 8]
# 			[0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1]]
# ExpNumの0行目は0-8の条件番号、1行目は0(button task)か1(voice task)
ExpNum = np.zeros((2, 18), dtype = int)
for l in range(18):
    if l < 9:
        ExpNum[0,l] = l
    else:
        ExpNum[0,l] = l-9
        ExpNum[1,l] = 1

#rng = np.random.default_rng()
#rng.shuffle(ExpNum, axis=1)

idx = 9

# save data
now = dt.datetime.now()
p_time = now.strftime('%Y%m%d-%H%M%S')

# to record beep and voice
# sampling frequency
fs = 44100  
# Max Duration in seconds
max_duration = 120
myrecording = None

# to show a cue word for each trial
img_path1 = "C:/Users/kumadalab/Desktop/COMMU/carlos/img/img1.jpg"
img_path2 = "C:/Users/kumadalab/Desktop/COMMU/carlos/img/img2.jpg"

d = {
        "waist_pitch": 0, "waist_yaw": 1, "left_arm_pitch": 2,
        "left_arm_roll": 3, "right_arm_pitch": 4, "right_arm_roll": 5,
        "head_pitch": 6, "head_roll": 7, "head_yaw": 8,
        "eye_pitch": 9, "left_eye": 10, "right_eye": 11,
        "eyelid": 12, "mouth": 13
    }
#----------------------------- GLOBAL VARIABLES END -----------------------------#


def show_images(img_path1, img_path2):
	global ExpNum
	cv_img1 = cv2.imread(img_path1,cv2.IMREAD_UNCHANGED)
	cv_img2 = cv2.imread(img_path2,cv2.IMREAD_UNCHANGED)

	cv_img1_resized = cv2.resize(cv_img1,  dsize=(400, 400))
	cv_img2_resized = cv2.resize(cv_img2,  dsize=(400, 400))

	# Create named windows with the WINDOW_NORMAL flag to allow resizing
	cv2.namedWindow("Images on Second Monitor", cv2.WINDOW_NORMAL)

	# Move the window to the second monitor (assuming it's the extended display)
	cv2.moveWindow("Images on Second Monitor", 4200, 800) 

	img_idx = 9
	for img_idx in range (18):
		if ExpNum[1,img_idx]==0:
			cv2.imshow("Images on Second Monitor", cv_img1_resized)
			while cv2.waitKey(0) != 32:
				time.sleep(2)
				pass
		else:
			cv2.imshow("Images on Second Monitor", cv_img2_resized)
			while cv2.waitKey(0) != 32:
				time.sleep(2)
				pass
		
		img_idx += 1

	cv2.destroyAllWindows()


def supervised_sleep(duration, function):
	num = int(duration * 100)
	for _ in range(num):
		flag = function()
		sleep(0.009)
		if flag:
			return True


def key_func():
	global is_space_pressed
	global is_q_pressed
	global idx
	global ExpNum
	global myrecording
	global beep_on
	global p_time

	# quit the program
	if keyboard.is_pressed('esc'): 
		init_pos()
		print("Terminating CommU")
		os._exit(-1)
	# trigger the keyboard function
	elif keyboard.is_pressed("space") and ExpNum[1,idx]==0:
		if not is_space_pressed: 
			if beep_on:
				is_space_pressed = True
				global trl_st, trl_dur
				trl_dur = time.time()-trl_st
				with open("C:/Users/kumadalab/Desktop/COMMU/carlos/button_data/dur_{}.txt".format(p_time), "a") as f:
					f.write(str(trl_dur) + ",{}".format(ExpNum[0,idx]) + "\n")
				print("Space detected")
				look_at_you()
				supervised_sleep(3, key_func)
				init_pos()
				is_space_pressed = False
				if idx < 17:
					idx += 1
					eval("condition{}()".format(ExpNum[0,idx]%3+1))
					return True
				else:
					init_pos()
					print("finishing the experiment")
					os._exit(-1)

	elif keyboard.is_pressed('q') and ExpNum[1,idx]==1:
		if not is_q_pressed:
			if beep_on:
				is_q_pressed = True
				print('Q detected')
				look_at_you()
				supervised_sleep(3, key_func)
				init_pos()

				sd.stop()
				print("Recording stopped")
				write('C:/Users/kumadalab/Desktop/COMMU/carlos/sound_data/output_{}_{}.wav'.format(p_time,ExpNum[0,idx]), fs, myrecording)
				        
				is_q_pressed = False
				if idx < 17:
					idx += 1
					eval("condition{}()".format(ExpNum[0,idx]%3+1))
					return True
				else:
					init_pos()
					print("finishing the experiment")
					os._exit(-1)
				

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
	move("eye_pitch", 0, .1)
	move("left_eye", -50, .1)
	move("right_eye", -50, .1)
	move("head_pitch", 8, .1)
	move("head_roll", 0, .1)
	move("head_yaw", 23, .1)
	move("waist_yaw", 7, .1)

 
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
		move("left_eye", 60, .1)
		move("right_eye", -40, .1) 
		move("left_eye", -50, .1)

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
	global ExpNum
	global idx
	global trl_st
	global myrecording
	global beep_on
	beep_on = False
	condition = [False]*4
	condition[1] = True
	print("Condition1")

	if ExpNum[1,idx]==1:
		myrecording = sd.rec(int(max_duration * fs), samplerate=fs, channels=2)
		print("Starting recording, press 'q' to stop...")

	for i in range(3):
		move("right_eye", 0, .1)
		move("left_eye", 0, .1)
		move("head_pitch", -10, .1)
		move("head_yaw", 0, .1)
		move("eye_pitch", -3, .1)
		move("head_roll", 0, .1)
		move("waist_yaw", 0, .1)
		reading(3)
		if ExpNum[0,idx]//3 == 2 and beep_on == False and i == 1:
			winsound.Beep(500, 200)
			trl_st = time.time()
			beep_on = True

		# st = time()
		for j in range(3):
			exploring_left()
			if ExpNum[0,idx]//3 == 0 and beep_on == False and i == 1:
				winsound.Beep(500, 200)
				trl_st = time.time()
				beep_on = True        
			supervised_sleep(3, key_func)
			
			exploring_right()
			if ExpNum[0,idx]//3 == 1 and beep_on == False and i == 1:
				winsound.Beep(500, 200)
				trl_st = time.time()
				beep_on = True
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
	global ExpNum
	global idx
	global trl_st
	global myrecording
	global beep_on
	beep_on = False
	condition = [False]*4
	condition[2] = True
	print("Condition2")

	if ExpNum[1,idx]==1:
		myrecording = sd.rec(int(max_duration * fs), samplerate=fs, channels=2)
		print("Starting recording, press 'q' to stop...")

	for i in range(3):
		move("right_eye", 0, .1)
		move("left_eye", 0, .1)
		move("head_pitch", -10, .1)
		move("head_yaw", 0, .1)
		move("eye_pitch", -3, .1)
		move("head_roll", 0, .1)
		move("waist_yaw", 0, .1)
		reading(3)
		if ExpNum[0,idx]//3 == 2 and beep_on == False and i == 1:
			winsound.Beep(500, 200)
			trl_st = time.time()
			beep_on = True
		
		# st = time()
		for j in range(3):
			communicative_left()
			if ExpNum[0,idx]//3 == 0 and beep_on == False and i == 1:
				winsound.Beep(500, 200)
				trl_st = time.time()
				beep_on = True
			supervised_sleep(3.445, key_func)

			communicative_right()
			if ExpNum[0,idx]//3 == 1 and beep_on == False and i == 1:
				winsound.Beep(500, 200)
				trl_st = time.time()
				beep_on = True
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
	move("left_eye", 0, .1)
	move("right_eye", 0, .1)
	move("head_roll", 0, .1)
	move("head_yaw", 40, .1)
	move("waist_yaw", 0, .1)

def working_right():
	move("head_pitch", -15, .1)
	move("head_yaw", 0, .1)
	move("eye_pitch", -3, .1)
	move("left_eye", 0, .1)
	move("right_eye", 0, .1)
	move("head_roll", 0, .1)
	move("head_yaw", -40, .1)
	move("waist_yaw", 0, .1) 

def condition3():
	global condition
	global ExpNum
	global idx
	global trl_st
	global myrecording
	global beep_on
	beep_on = False
	condition = [False]*4
	condition[3] = True
	print("condition3")

	if ExpNum[1,idx]==1:
		myrecording = sd.rec(int(max_duration * fs), samplerate=fs, channels=2)
		print("Starting recording, press 'q' to stop...")

	for i in range(3):
		#move("right_eye", 0, .1)
		#move("left_eye", 0, .1)
		move("head_pitch", -10, .1)
		move("head_yaw", 0, .1)
		move("eye_pitch", -3, .1)
		move("head_roll", 0, .1)
		reading(3)
		if ExpNum[0,idx]//3 == 2 and beep_on == False and i == 1:
			winsound.Beep(500, 200)
			trl_st = time.time()
			beep_on = True
		# st = time()

		for j in range(6):
			working_left()
			if ExpNum[0,idx]//3 == 0 and beep_on == False and i == 1:
				winsound.Beep(500, 200)
				trl_st = time.time()
				beep_on = True
			supervised_sleep(0.5, key_func)

			working_right()
			if ExpNum[0,idx]//3 == 1 and beep_on == False and i == 1:
				winsound.Beep(500, 200)
				trl_st = time.time()
				beep_on = True
			supervised_sleep(0.5, key_func)

		# cur = time()-st
		# with open("C:/Users/kumadalab/Desktop/COMMU/Shiro/duration_cond3.txt", "a") as f:
		#      f.write(str(cur) + "\n")
	init_pos()
    

if __name__ == '__main__':
	t1 = threading.Thread(target=connect2socket)
	#t1.setDaemon (True)
	t1.start()

	t2 = threading.Thread(target=show_images, args=(img_path1, img_path2))
	t2.start()

	time.sleep(2)
	print('send motion commands')

	while flag_quit == 0: 
		if flag_connected == 1:


			init_pos()
			
			if ExpNum[0,idx]%3 == 0:
				condition1()
			elif ExpNum[0,idx]%3 == 1:
				condition2()
			elif ExpNum[0,idx]%3 == 2:
				condition3()


		flag_quit = 1

	t1.join()
	t2.join()
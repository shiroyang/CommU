"""
20230829
feature: updated log function


"""
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
import datetime
import numpy as np
import glob
from pydub.generators import Sine
from pydub.playback import play
sys.setrecursionlimit(10**8)

  
#----------------------------- GLOBAL VARIABLES START -----------------------------#

# The whole experiment will be conducted 3 times.
REP_NUM = 3
# Record the current Exp Number with a global varible
CURRENT_EXP_NUM = 0
# Each experiment has 3 CommU states * 3 beep time timings * 2 response conditinos = 18 trials
TRIAL_CNT = 18 
# The duration
IMG_DURATION = 20



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

ExpNum = []
for i in range(18):
    ExpNum.append([i%9, i//9])
random.shuffle(ExpNum)
ExpNum = np.array(ExpNum).transpose()
print(ExpNum)
idx = 0

# save data
now = datetime.datetime.now()
p_time = now.strftime('%Y%m%d-%H%M%S')

# to record beep and voice
# sampling frequency
# fs = 44100  
fs = 16000  
# Max Duration in seconds
max_duration = 120
myrecording = None

# to show a cue word for each trial
cue_path1 = "C:/Users/kumadalab/Desktop/COMMU/carlos/img/cue/cue1.jpg"
cue_path2 = "C:/Users/kumadalab/Desktop/COMMU/carlos/img/cue/cue2.jpg"
img_list = glob.glob("C:/Users/kumadalab/Desktop/COMMU/carlos/img/*.jpg")
    
var_path = "C:/Users/kumadalab/Desktop/COMMU/carlos/shared_variables/tmp.txt"

log_path = "C:/Users/kumadalab/Desktop/COMMU/carlos/log_data/log_{}.txt".format(p_time)

d = {
        "waist_pitch": 0, "waist_yaw": 1, "left_arm_pitch": 2,
        "left_arm_roll": 3, "right_arm_pitch": 4, "right_arm_roll": 5,
        "head_pitch": 6, "head_roll": 7, "head_yaw": 8,
        "eye_pitch": 9, "left_eye": 10, "right_eye": 11,
        "eyelid": 12, "mouth": 13
    }
#----------------------------- GLOBAL VARIABLES END -----------------------------#

def log(func):
    def wrapper(*args, **kwargs):
        log_path = "C:/Users/kumadalab/Desktop/COMMU/carlos/log_data/log_{}.txt".format(p_time)
        
        try:
            with open(log_path, 'a') as f:
                f.write("{}   {}\n".format(datetime.datetime.now(), func.__name__))
        except Exception as e:
            print(f"Failed to log information: {e}")
        
        return func(*args, **kwargs)
    return wrapper


@log
def play_tone(frequency, duration):
    tone = Sine(frequency)
    play(tone.to_audio_segment(duration * 1000))  # Duration is in milliseconds



def show_images(cue_path1, cue_path2):
	global ExpNum
	global beep_on, is_q_pressed, is_space_pressed
	global IMG_DURATION

	cv_cue1 = cv2.imread(cue_path1,cv2.IMREAD_UNCHANGED)
	#cv_cue2 = cv2.imread(cue_path2,cv2.IMREAD_UNCHANGED)
	cv_cue1_resized = cv2.resize(cv_cue1,  dsize=(400, 400))
	#cv_cue2_resized = cv2.resize(cv_cue2,  dsize=(400, 400))
	
	# trial number across three conditions
	# ExpNum = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 0, 1, 2, 3, 4, 5, 6, 7, 8]
	# 			[0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1]]
	# ExpNumの0行目は0-8の条件番号、1行目は0(button task)か1(voice task)

	img_idx = [i for i in range(9)]
	random.shuffle(img_idx)

	for cue_idx in range (TRIAL_CNT):
		cv2.namedWindow("Images on Second Monitor", cv2.WINDOW_NORMAL)
		cv2.moveWindow("Images on Second Monitor", 3800, 200)
		cv2.resizeWindow("Images on Second Monitor", 1200, 800)
		time.sleep(7)

		st_time = time.time()

		if ExpNum[1, cue_idx] == 0:
			with open(log_path, 'a') as f:
				f.write("{}   Showing img BUTTON\n".format(datetime.datetime.now()))
			while True:
				if time.time() - st_time < IMG_DURATION:
					
					cv2.imshow("Images on Second Monitor", cv_cue1_resized)
					key = cv2.waitKey(10)
				else:
					cv2.destroyAllWindows()
				
				with open(var_path, "r") as f:
					change_img = f.read()

				if "1" in change_img:
					print("Changing img")
					with open(var_path, "w") as f:
						f.write("0")
					break
				

		else:
			
			cur_img_idx = img_idx.pop()
			cv_img_file = cv2.imread(img_list[cur_img_idx])
			cv_img_resized = cv2.resize(cv_img_file,  dsize=(1000, 1000))

			with open(log_path, 'a') as f:
				f.write("{}   Showing img {}\n".format(datetime.datetime.now(), cur_img_idx+1))

			while True:
				if time.time() - st_time <= IMG_DURATION:
					
					cv2.imshow("Images on Second Monitor", cv_img_resized)
					key = cv2.waitKey(10)
				else:
					cv2.destroyAllWindows()
				
				with open(var_path, "r") as f:
					change_img = f.read()

				if "1" in change_img:
					print("Changing img")
					with open(var_path, "w") as f:
						f.write("0")
					break
				
		

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

				with open(log_path, 'a') as f:
					f.write("{}   is_space_pressed = True\n".format(datetime.datetime.now()))
				is_space_pressed = True
				global trl_st, trl_dur
				trl_dur = time.time()-trl_st
				with open("C:/Users/kumadalab/Desktop/COMMU/carlos/button_data/dur_{}.txt".format(p_time), "a") as f:
					f.write(str(trl_dur) + ",{}".format(ExpNum[0,idx]) + "\n")
				print("Space detected")
				
				with open(var_path, "w") as f:
					f.write("1")

				look_at_you()
				supervised_sleep(3, key_func)
				init_pos()
				beep_on = False
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
				with open(log_path, 'a') as f:
					f.write("{}   is_q_pressed = True\n".format(datetime.datetime.now()))
				is_q_pressed = True
				print('Q detected')

				with open(var_path, "w") as f:
					f.write("1")

				look_at_you()
				supervised_sleep(3, key_func)
				init_pos()

				sd.stop()
				print("Recording stopped")
				write('C:/Users/kumadalab/Desktop/COMMU/carlos/sound_data/output_{}_{}_{}.wav'.format(p_time,ExpNum[0,idx],idx), fs, myrecording)
				
				beep_on = False
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

def move(joint_name, val, sleep_time=.1, velocity=1000):
	priority=3
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

	with open(var_path, "w") as f:
		f.write("0")

	print("Initialized")

@log
def look_at_you():
	print("look at you")
	move("eye_pitch", 0, .1)
	move("left_eye", -50, .1)
	move("right_eye", -50, .1)
	move("head_pitch", 8, .1)
	move("head_roll", 0, .1)
	move("head_yaw", 23, .1)
	move("waist_yaw", 7, .1)

@log
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

		move("right_eye", -40, .01, velocity=600) 
		move("left_eye", -50, .01, velocity=600)
		supervised_sleep(.5, key_func)	

		move("right_eye", 70, .01, velocity=900)
		move("left_eye", 60, .01, velocity=900)
		supervised_sleep(.8, key_func)


		

## condition1
# 8.826 sec / loop
# left_eye, right_eye under consideration
@log
def exploring_left():
    move("eye_pitch", 18, .1)
    move("left_eye", -25, .1)
    move("right_eye", -3, .1)
    move("head_pitch", 18, .1)
    move("head_roll", -6, .1)

    move("head_yaw", 15, .1)
    move("waist_yaw", 15, .1)
    

@log
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
		# myrecording = sd.rec(int(max_duration * fs), samplerate=fs, channels=2)
		myrecording = sd.rec(int(max_duration * fs), samplerate=fs, channels=1, dtype='int16')
		with open(log_path, 'a') as f:
			f.write("{}   Start recording at Condition1\n".format(datetime.datetime.now()))

		print("Starting recording, press 'q' to stop...")


	for i in range(6):
		move("right_eye", 0, .1)
		move("left_eye", 0, .1)
		move("head_pitch", -10, .1)
		move("head_yaw", 0, .1)
		move("eye_pitch", -3, .1)
		move("head_roll", 0, .1)
		move("waist_yaw", 0, .1)
		reading(3)
		if ExpNum[0,idx]//3 == 2 and beep_on == False and i == 1:
			play_tone(500, 0.2)
			trl_st = time.time()

			beep_on = True

		# st = time()
		for j in range(3):
			exploring_left()
			if ExpNum[0,idx]//3 == 0 and beep_on == False and i == 1:
				play_tone(500, 0.2)
				trl_st = time.time()

				beep_on = True   
			supervised_sleep(3, key_func)
			
			exploring_right()
			if ExpNum[0,idx]//3 == 1 and beep_on == False and i == 1:
				play_tone(500, 0.2)
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
@log
def communicative_left():
    move("eye_pitch", 0, .1)
    move("left_eye", -50, .1)
    move("right_eye", -50, .1)
    move("head_pitch", 8, .1)
    move("head_yaw", 23, .1)
    move("waist_yaw", 7, .1)

@log
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
		# myrecording = sd.rec(int(max_duration * fs), samplerate=fs, channels=2)
		myrecording = sd.rec(int(max_duration * fs), samplerate=fs, channels=1, dtype='int16')
		with open(log_path, 'a') as f:
			f.write("{}   Start recording at Condition2\n".format(datetime.datetime.now()))
		print("Starting recording, press 'q' to stop...")

	for i in range(6):
		move("right_eye", 0, .1)
		move("left_eye", 0, .1)
		move("head_pitch", -10, .1)
		move("head_yaw", 0, .1)
		move("eye_pitch", -3, .1)
		move("head_roll", 0, .1)
		move("waist_yaw", 0, .1)
		reading(3)
		if ExpNum[0,idx]//3 == 2 and beep_on == False and i == 1:
			play_tone(500, 0.2)
			trl_st = time.time()
	
			beep_on = True
		
		# st = time()
		for j in range(3):
			communicative_left()
			if ExpNum[0,idx]//3 == 0 and beep_on == False and i == 1:
				play_tone(500, 0.2)
				trl_st = time.time()
				beep_on = True
		
			supervised_sleep(3.445, key_func)

			communicative_right()
			if ExpNum[0,idx]//3 == 1 and beep_on == False and i == 1:
				play_tone(500, 0.2)
				trl_st = time.time()

				beep_on = True
			supervised_sleep(3.445, key_func)

        # cur = time()-st
        # with open("C:/Users/kumadalab/Desktop/COMMU/Shiro/duration_cond2.txt", "a") as f:
        #      f.write(str(cur) + "\n")
		init_pos()


## condition3
# 1.74sec?
@log
def working_left():
	move("head_pitch", -15, .1)
	move("head_yaw", 0, .1)
	move("eye_pitch", -3, .1)
	move("left_eye", 0, .1)
	move("right_eye", 0, .1)
	move("head_roll", 0, .1)
	move("head_yaw", 40, .1)
	move("waist_yaw", 0, .1)

@log
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
	# print("cond3: beep_on = False, 479")
	beep_on = False
	condition = [False]*4
	condition[3] = True
	print("condition3")

	if ExpNum[1,idx]==1:
		# myrecording = sd.rec(int(max_duration * fs), samplerate=fs, channels=2)
		myrecording = sd.rec(int(max_duration * fs), samplerate=fs, channels=1, dtype='int16')
		with open(log_path, 'a') as f:
			f.write("{}   Start recording at Condition3\n".format(datetime.datetime.now()))
		print("Starting recording, press 'q' to stop...")

	for i in range(6):
		#move("right_eye", 0, .1)
		#move("left_eye", 0, .1)
		move("head_pitch", -10, .1)
		move("head_yaw", 0, .1)
		move("eye_pitch", -3, .1)
		move("head_roll", 0, .1)
		reading(3)
		if ExpNum[0,idx]//3 == 2 and beep_on == False and i == 1:
			play_tone(500, 0.2)
			trl_st = time.time()
	
			beep_on = True
		# st = time()

		for j in range(6):
			working_left()
			if ExpNum[0,idx]//3 == 0 and beep_on == False and i == 1:
				play_tone(500, 0.2)
				trl_st = time.time()

				beep_on = True
			supervised_sleep(0.5, key_func)

			working_right()
			if ExpNum[0,idx]//3 == 1 and beep_on == False and i == 1:
				play_tone(500, 0.2)
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

	t2 = threading.Thread(target=show_images, args=(cue_path1, cue_path2))
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
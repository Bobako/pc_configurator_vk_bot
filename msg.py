import random
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

from file_processer import read_random_ids
from file_processer import write_random_id

def snd(vk,user,msg,file_name,payload, keyboard=None, attachment = None):      # sends a message
	
	#i = random.randint(-9223372036854775808,9223372036854775807)
		
	sent_i =0
	#try:
	sent_i = vk.method('messages.send', {'user_id':user,'random_id':sent_i, 'message': msg, 'keyboard':keyboard,'attachment':attachment, 'payload':payload})
	#except Exception:
	#	pass
	if sent_i != 0:
		write_random_id(sent_i, file_name)
		return True  #Succes
	else:
		return False #error


def rcv(vk, file_name):										#waits for a message, and returns it in json format dict
	longpoll = VkLongPoll(vk)
	random_ids = read_random_ids(file_name)
	msg = {'user':None,
		   'msg':None,
		   'random_id':None,
		   'payload':None
		   }												
	for event in longpoll.listen():
		if event.type == VkEventType.MESSAGE_NEW:
			if int(event.random_id) in random_ids:
				pass
			else:
				msg['user']=str(event.user_id)
				msg['msg']=event.text
				msg['random_id']=event.random_id
				
				try:msg['payload'] = event.payload
				except Exception: pass
				
				return msg
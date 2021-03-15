import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from threading import Thread
import openpyxl
import time
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import msg
import time
import traceback
import sys
import file_processer

import parts

class Bot(Thread):

	filesys = {"ids":"ids.txt",				#used messages random ids
			   "settings":"settings.json",	#configuration file (json format)
			   "logs":"log.txt",			#logs
			   "configs":"configs.json",	#prefab pc configs database
			   #"rqsts":"rqsts.xlsx",
			   "sessions":"sessions.json",
			   "keyboards":"keyboards.json"}

	alive = True
	sessions= []



	def __init__(self):
		self.token = '***'
		self.vk = vk_api.VkApi(token = self.token)

		self.load_keyboards()
		self.load_configs()
		Thread.__init__(self)
		self.start()

	def load_keyboards(self):
		self.keyboards = file_processer.read_json(self.filesys['keyboards'])
		for key in list(self.keyboards.keys()):
			self.keyboards[key]=file_processer.to_json(self.keyboards[key])

	def load_configs(self):
		self.configs = file_processer.read_json(self.filesys['configs'])['configs']
		
 
	def send(self,user,message,payload = None, keyboard = None):	
		if self.alive: 
			return msg.snd(self.vk,user,message,self.filesys["ids"],payload,keyboard = keyboard)								#vk,user,msg,

	def receive(self):
		try:
			return msg.rcv(self.vk,self.filesys["ids"])	
		except Exception:
			self.alive = False
			return											

	def new_session(self,user,type_,back = None):
		if self.alive: self.sessions.append(Session(user,type_,self,back))

	def await_request(self):
		while self.alive:
			
			last_msg = self.receive()

			if last_msg!= None:

				if last_msg['msg'].lower() in ['начать']:
					self.new_session(last_msg['user'],'greetings')

				elif last_msg['msg'].lower() in ['конфигуратор']:
					self.new_session(last_msg['user'], 'configurator')

				elif last_msg['msg'].lower() in ['сборки']:
					self.new_session(last_msg['user'], 'configs')

				elif last_msg['msg'].lower() in ['менеджер']:
					self.new_session(last_msg['user'], 'manager')
		
				elif last_msg['msg'].lower() in ['подобрать']:
					self.new_session(last_msg['user'], 'suit')

				elif self.check_backup(last_msg):
					self.restore_session(str(last_msg['user']))



	def check_backup(self, msg):
		active_users = [str(session.user) for session in self.sessions]
		backuped_users = file_processer.read_json(self.filesys['sessions']).keys()
		user = str(msg['user'])

		if (user in backuped_users) and (not(user in active_users)):
			return True
		else: 
			return False

	def restore_session(self,user):
		backup = file_processer.read_json(self.filesys['sessions'])[user]
		self.new_session(str(user),backup['type_'],backup)
		



	def session_suicide(self,id_):
		try:
			return self.sessions.pop(id_)
		except Exception:
			pass

	def run(self):
		self.await_request()

	
class Session(Thread):
	type_ = None                                          #
	step = 0											  #
	user = None											  #
	
	bot = None
	prices = False										  #
	progress = True										  #
	id_  = 0
	keyboard = None										
	returned = False
	config = {}											  #
	requirements = None                                   #

	hdd = {'512GB':'512GB - 2300₽','1TB':'1TB - 2500₽','2TB':'2TB - 3700₽'}
	hdd_prices = {'512GB':2300,'1TB':2500,'2TB':3700}

	ssd = {'0':'Без твердотельного накопителя','120GB':'120GB - 1400₽','240GB':'240GB - 2100₽','500GB':'500GB - 4300₽','1TB':'1TB - 7000₽'}
	ssd_prices = {'0':0,'120GB':1400,'240GB':2100,'500GB':4300,'1TB':7000}

	def __init__(self,user,type_,bot, back):
		self.type_ = type_
		self.user = user
		self.bot = bot
		self.requirements = parts.get_requirements()
		self.id_ = len(bot.sessions)-1

		if back!=None:
			self.step = back['step']
			self.prices = back['prices']
			self.progress = back['progress']
			self.config = back['config']
			self.requirements = back['requirements']

		Thread.__init__(self)
		self.start()

	def run(self):
		if self.type_ == 'greetings':
			self.greetings()
		if self.type_ == 'configurator':
			self.configurator()
		if self.type_ == 'configs':
			self.configs()
		if self.type_ == 'manager':
			self.manager()
		if self.type_ == 'suit':
			self.suit()



		self.bot.session_suicide(self.id_)

	def set_keyboard(self, k_type):
		if k_type == None:
			self.keyboard = None
		else:
			self.keyboard = self.bot.keyboards[k_type]


	def im_choice(self,start_msg,ids,names):
		
		msg = start_msg

		for i in range(len(ids)):
			msg += '\n' + str(i+1) +'. ' + str(names[i])

		self.im_send(msg)

		while True:
			answer = self.im_receive()
			if not (self.bot.alive):
				self.step = 100
				return

			
			answer = answer['msg']
			if answer.lower() == 'цены':
				self.prices = not(self.prices)
				if self.prices:
					self.im_send('Цены теперь будут отображаться.')
				else:
					self.im_send('Цены теперь не будут отображаться.')
				self.step-=1
				self.returned = True
				return 

			elif answer.lower() == 'закончить':
				self.set_keyboard('greetings')
				self.im_send('Сессия завершена.')
				self.remove_backup()

				self.step=100
				return 	

			elif answer.lower()=='назад':
				self.step-=2
				return

			elif answer.lower()=='прогресс':
				self.progress = not(self)
				if self.progress:
					self.im_send('Прогресс теперь будет отображаться.')
				else:
					self.im_send('Прогресс теперь не будет отображаться.')
				self.step-=1
				return

			else:
				try:
					answer = int(answer)
					
				except Exception:
					self.im_send("Введите номер выбранного варианта.")
				else:
					
					if answer in list(range(1,len(ids)+1)):
						
						chosen = ids[answer-1]
						
						return chosen
					else:
						self.im_send("Введен номер несуществующего элемента. Повторите ввод.")
	
				

				

		#return self.bot.choice(start_msg,ids,names,self.user, self.id_)


	def im_choice_part(self,start_msg, parts):
		if parts == []:
			self.im_send('Ни одной подходящей комплектующей не найдено. Попробуйте изменить свой выбор на одном из предыдущих шагов.')
			self.step-=2
			return 
		msg = start_msg
		for i in range (len(parts)):
				msg+='\n'+str(i+1)+'. '+ str(parts[i]['name'])
				if self.prices:
					msg+='   -   ' + str(parts[i]['price']) + "₽"
		self.im_send(msg)

		while True:
			answer = self.im_receive()
			if not (self.bot.alive):
				self.step = 100
				return
			
			answer = answer['msg']
			if answer.lower() == 'цены':
				self.prices = not(self.prices)
				if self.prices:
					self.im_send('Цены теперь будут отображаться.')
				else:
					self.im_send('Цены теперь не будут отображаться.')
				self.step-=1
				self.returned = True
				return

			elif answer.lower() == 'закончить':
				self.set_keyboard('greetings')
				self.im_send('Сессия завершена.')
				self.remove_backup()
				self.step=100
				return 

			elif answer.lower()=='назад':
				self.step-=2
				return

			elif answer.lower()=='прогресс':
				self.progress = not(self)
				if self.progress:
					self.im_send('Прогресс теперь будет отображаться.')
				else:
					self.im_send('Прогресс теперь не будет отображаться.')
				self.step-=1
				return




			else:
				try:
					
					answer = int(answer)
				except Exception:
					self.im_send("Введите номер выбранного варианта.")
				else:
					
					if answer in range(1,len(parts)+1):
						chosen = parts[answer-1]
						return chosen
					else:
						self.im_send("Введен номер несуществующего элемента. Повторите ввод.")
	
				

		
		


		#return self.bot.choice_part(start_msg, parts, self.user, id_)

	def im_send(self,msg):
		self.bot.send(self.user,msg, keyboard = self.keyboard)

	def im_receive(self):
		while True:
			receive = self.bot.receive()
			if receive['user']==self.user:
				return receive

	def greetings(self):
		self.set_keyboard('greetings')
		msg = "Это наш бот. Его команды: \nСоздать сборку ПК самому - конфигуратор \nВоспользоваться имеющейся - сборки \nПодобрать сборку исходя из поставленных задач - подобрать (в разработке)\n Связаться с менеджером - менеджер"
		self.im_send(msg)

	def configs(self):
		while self.step <5:
			if self.step in range(4):
				self.set_keyboard('configs')

			if self.step ==0:
				temp= self.im_choice('Добро пожаловать! Здесь вы можете подобрать готовую сборку ПК. \n-\nЧтобы выбрать, отправляйте номер возможного вариантаиз списка.\n-\nКоманды: \nназад - отменить последний выбор.\nзакончить - сбросить все решения и завершить сессию.\n-\nВыберите ценовую категорию:',[[30000,50000],[50001,70000],[70001,100000]],['30 000₽ - 50 000₽','50 000₽ - 70 000₽','70 000₽ - 100 000₽'])
				if temp!=None: self.config['config_price_range'] = temp
			elif self.step == 1:
				temp= self.im_choice('Выберите производителя:',['amd','intel',None],['AMD','Intel','Не имеет значения'])
				if temp!=None: self.config['config_proizv'] = temp
			elif self.step == 2:
				temp= self.im_choice('Выберите сборку:',self.find_configs()[0],self.find_configs()[1])
				if temp!=None: self.config['config_chosen'] = temp
			elif  self.step ==3:
				temp = self.im_send('Ваша сборка:\n'+self.config['config_chosen']['main'])
				self.set_keyboard('confirm')
				temp = self.im_choice('Вы хотите подтвердить выбор и отправить запрос на сборку менеджеру?',[False,True],['Нет','Да'])
				if temp!= None:self.config['config_confirm'] = temp
				if temp: self.im_send('Запрос отправлен.')

			elif self.step == 4:
				self.set_keyboard('greetings')
				self.im_send('Спасибо, что воспользовались нашим ботом!')
				return 0
			if self.step<4:self.backup()
			self.step+=1

	def manager(self):
		self.im_send('Запрос менеджеру отправлен. Он свяжется с вами в ближейшее время.')

	def suit(self):
		self.im_send('Функция в разработке. Свяжитесь с менеджером.')

	def configurator(self):
		
		while self.step < 100:
			if self.step in range(15):
				self.set_keyboard('configurator')
			if self.step == 0:
				temp = self.im_choice('Добро пожаловать! Это конфигуратор ПК. Здесь вы можете подобрать комплектующие для вашего будущего компьютера. \n-\nЧто бы выбрать, отправляйте номер комплектущей из списка.\n✓ - знак, что элемент проверен и рекомендован для своей ценовой категории.\n-\nКоманды: \nназад - отменить последний выбор.\nзакончить - сбросить все решения и завершить сессию.\nцены - показать/спрятать цены комплектующих.\n-\nпрогресс - показать/спрятать отображение прогресса выбора элементов после каждого шага\n-\nВыберите производителя:',['amd','intel'],['AMD','Intel'])
				
				if temp!= None: self.requirements = parts.update_requirements(self.requirements, parameter = {'proizv_chosen':temp})
				
			elif self.step == 1:
				
				temp = self.im_choice_part('Вашему выбору удовлетворяют такие процессоры, выберите один из них:',parts.find_all('cpu',self.requirements))
				if temp!= None:
					self.requirements = parts.update_requirements(self.requirements, part = temp)
					self.config['cpu'] = temp
			
			elif self.step ==2:
				temp = self.im_choice_part('Этот процессор можно установить на любую из приведенных ниже материнских плат. Выберите одну их них:',parts.find_all('motherboard',self.requirements))
				if temp!= None:
					self.requirements = parts.update_requirements(self.requirements, part = temp)
					self.config['motherboard'] = temp

			elif self.step ==3:
				temp = self.im_choice('Выберите производителя графического чипа:',['nvidia','radeon'],['NVidia','Radeon'])
				if temp!= None:self.requirements = parts.update_requirements(self.requirements, parameter = {'gpu_proizv_chosen':temp})

			elif self.step ==4:
				temp = self.im_choice('Выберите объем видеопамяти видеокарты:',[4,6,8,11],['4GB','6GB','8GB','11GB'])
				if temp!= None:self.requirements = parts.update_requirements(self.requirements, parameter = {'gpu_memory_chosen':temp})

			elif self.step ==5:
				temp = self.im_choice_part('Выберите видеокарту',parts.find_all('gpu',self.requirements))
				if temp!= None:
					self.requirements = parts.update_requirements(self.requirements, part = temp)
					self.config['gpu'] = temp

			elif self.step ==6:
				ports = int(self.requirements['max_ram_ports'])
				temp = self.im_choice('Выберите количество планок ОЗУ:',list(range(1,ports+1)),list(range(1,ports+1)))
				if temp!= None:self.requirements = parts.update_requirements(self.requirements, parameter = {'ram_ports_chosen':temp})

			elif self.step ==7:
				mrm = int(self.requirements['max_ram_mem'])
				mems = [8,16,32,64,128]
				mems_ = []
				for mem in mems:
					if mem <=mrm: mems_.append(mem)


				temp = self.im_choice('Выберите суммарный объем памяти ОЗУ:',mems_,mems_)
				if temp!= None:self.requirements = parts.update_requirements(self.requirements, parameter = {'ram_mem_chosen':temp})	

			elif self.step == 8:
				temp = self.im_choice_part('Выберите комплект ОЗУ:',parts.find_all('ram',self.requirements))
				if temp!= None:
					self.requirements = parts.update_requirements(self.requirements, part = temp)
					self.config['ram'] = temp

			elif self.step ==9:
				temp = self.im_choice_part('Выберите кулер',parts.find_all('coolek',self.requirements))
				if temp!= None:
					self.requirements = parts.update_requirements(self.requirements, part = temp)
					self.config['coolek'] = temp


			elif self.step ==10:
				temp = self.im_choice_part('Выберите корпус',parts.find_all('korpus',self.requirements))
				if temp!= None:self.config['korpus'] = temp
				

			elif self.step ==11:
				
				temp = self.im_choice_part('Выберите блок питания',parts.find_all('bp',self.requirements))
				if temp!= None:self.config['bp'] = temp

			elif self.step ==12:
				temp = self.im_choice('Выберите объем жесткого диска:', list(self.hdd.keys()),list(self.hdd.values()))
				if temp!= None:self.config['hdd_mem'] = {'name':temp,
														 'price':self.hdd_prices[temp]}

			elif self.step==13:
				temp = self.im_choice('Выберите объем твердотельного накопителя:',list(self.ssd.keys()),list(self.ssd.values()))
				if temp!= None:self.config['ssd_mem'] = {'name':temp,
														 'price':self.ssd_prices[temp]}

			elif self.step==14:
				self.im_send('Дополнительные требования к сборке? (При необходимости)')
				temp = self.im_receive()
				if temp!= None:self.config['comment'] = temp['msg']	

			elif self.step==15:
				self.set_keyboard('confirm')
				temp = self.im_choice('Вы хотите подтвердить выбор и отправить запрос на сборку менеджеру?',[False,True],['Нет','Да'])
				if temp!= None:self.config['confirm'] = temp
				if temp: self.im_send('Запрос отправлен.')

			elif self.step == 16:
				self.set_keyboard('greetings')
				self.im_send('Спасибо, что воспользовались нашим, нет блять, не нашим, конфигуратором!')
				self.adm_send(self.form_order())
				self.remove_backup()

				return 0


			self.step+=1
			if self.step<16:self.backup()
			if self.progress and not(self.step in [0,1,4,5,7,8,16,100,101]) and not(self.returned):
				self.im_send('Пройдено '+str(self.step)+' шагов из 15. Стоимость выбранных комплектующих составляет '+str(self.count_price())+'₽')
			self.returned = False
	def count_price(self):
		s = 0
		for i in self.config:
			
			if i != 'confirm' and i != 'comment':
				s+= int(self.config[i]['price'])
		return s

	def find_configs(self):
		price_range = self.config['config_price_range']
		proizv = self.config['config_proizv']
		configs = self.bot.configs
		found_configs = []
		for config in configs:
			if (config['proizv']==proizv or config['proizv']==None) and (int(config['price']) in list(range(price_range[0],price_range[1]))):
				found_configs.append(config)

		return [found_configs,[c['name'] for c in found_configs]]

	def form_order(self):
		s = 'https://vk.com/id'+self.user +'\n -\nPrice - ' + self.count_price + '\n -\n'

		for piece in self.config:
			try:
				name = self.config[piece]['name']
			except: name = self.config[piece]
			s+= piece + ' - ' +str(name)+'\n'
		return s 

	def adm_send(self,msg):
		for admin in [368571771]:
			self.bot.send(admin,msg)

	def backup(self):
		dict_ = {str(self.user):{
			'type_':self.type_,
			'step':self.step,
			'prices':self.prices,
			'progress':self.progress,
			'config':self.config,
			'requirements':self.requirements
		}}

		file_processer.write_json(self.bot.filesys['sessions'], dict_)


	def remove_backup(self):
		file_processer.remove_json_key(self.bot.filesys['sessions'],str(self.user))





class Bot_Controller(Thread):


	restart_time = 3600


	def __init__(self):
		self.bot = Bot()
		self.count = 0
		Thread.__init__(self)
		self.in_time = time.mktime(time.localtime())
		self.start()
	def run(self):
		while True:
			time.sleep(10)
			if not(self.check_bot()):
				self.restart_bot()

	def check_bot(self):
		return (self.bot.alive and self.restart_time> self.delta()-self.restart_time*self.count) 


	def restart_bot(self):
		print(time.strftime("%d.%m.%Y  %H:%M  -  ",time.localtime()),'Restarting...')
		self.bot.alive = False
		self.bot = Bot()
		self.count +=1

	def info(self):
		print('Active for',self.delta(), 'seconds.')

	def delta(self):
		return time.mktime(time.localtime()) - self.in_time 


if __name__ == '__main__':
	bob = Bot_Controller()
	


	


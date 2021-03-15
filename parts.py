from file_processer import read_xlsx
import openpyxl

def get_parts(file_name = 'db_v2.xlsx',sheet_name = "Sheet1"):				#gets parts from bd (by mal)(for amtech vk bot )
	book = read_xlsx(file_name)
	stook = book[sheet_name]
	parts = []
	MAXIM = len(stook)
	for row in range (1,len(stook)+1):
		line = stook[str(row)]
		if line['id'] == None:
			MAXIM = row-1

	for row in range (1,MAXIM+1):
		row = str(row)
		line = stook[row]
		parts.append(line)
	return(parts)

parts = get_parts()
def get_requirements():
	requirements = {'socket': None,
				'tdp': None,
				'max_ram_freq_from_cpu': None,
				'max_ram_freq_from_mb': None,
				'max_ram_ports': None,
				'max_ram_mem': None,
				'cpu_pins': None,
				'gpu_length': None,
				'cooler_height': None,
				'gpu_wt': None,
				'proizv_chosen': None,
				'gpu_proizv_chosen': None,
				'gpu_memory_chosen': None,
				'ram_ports_chosen': None,
				'ram_mem_chosen': None,
				'n_pin6': None,
				'n_pin8': None,
				}
	return requirements




def find_all(ptype, requirements, parts = parts):
	found = []
	for part in parts:
		if part['ptype'] == ptype:
			if check(ptype, requirements, part):
				found.append(part)

	return found


def check(ptype, requirements, part):
	if ptype == "cpu":
		return (part['proizv'] == requirements['proizv_chosen'])
	
	elif ptype == "motherboard":
		return (part['socket'] == requirements['socket'])

	elif ptype == "gpu":

		return (part['mem']==requirements['gpu_memory_chosen']) and (part['proizv']==requirements['gpu_proizv_chosen'])

		
	elif ptype == "ram":
		return (part['freq'] <=requirements['max_ram_freq_from_cpu'] and part['freq'] <=requirements['max_ram_freq_from_mb'] and part['mem'] == requirements['ram_mem_chosen'] and part['ports'] == requirements['ram_ports_chosen'])
			
	elif ptype == "coolek":
		return (part['tdp'] >=requirements['tdp'])
	
	elif ptype == "korpus":
		print('korpus dlina',part['dlina'], 'gpu length',requirements['gpu_length'],'corp vys',part['vys'],'cool h',requirements['cooler_height'])
		return (part['dlina']>requirements['gpu_length'] and part['vys']>requirements['cooler_height'])

	elif ptype == "bp":
		temp_part = part
		cpu_pins = requirements['cpu_pins']
		while cpu_pins>0:

			if cpu_pins>=8:
				temp_part['n_pin8']-=1
				cpu_pins-=8
			else: 
				temp_part['n_pin6']-=1
				cpu_pins-=6
		
		return (part['wt']>=requirements['tdp']+300 and temp_part['n_pin6']>=requirements['n_pin6'] and temp_part['n_pin8']>=requirements['n_pin8'])


def update_requirements(requirements, part = None, parameter = None):
	if part!= None:
		
		ptype = part['ptype']
		if ptype == 'cpu':
			requirements['socket'] = part['socket']
			requirements['tdp'] = part['tdp']
			requirements['max_ram_freq_from_cpu'] = part['freq']
		elif ptype == 'motherboard':
			requirements['max_ram_freq_from_mb'] = part['freq']
			requirements['max_ram_ports'] = part['ports']
			requirements['max_ram_mem'] = part['mem']
			requirements['cpu_pins'] = part['CPU pw']
		elif ptype == 'gpu':
			requirements['n_pin6'] = part['n_pin6']
			requirements['n_pin8'] = part['n_pin8']
			requirements['gpu_length'] = part['dlina']
			requirements['gpu_wt'] = part['wt']
		elif ptype == 'coolek':
			requirements['cooler_height'] = part['vys']
	else:

		
		requirements[list(parameter.keys())[0]] = parameter[list(parameter.keys())[0]]	
		

	return requirements


 #pinCPUGPU
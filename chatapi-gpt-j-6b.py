#!/bin/python3
# -*- coding: utf-8 -*-

from datetime import datetime
import os
import time
import torch
from enum import Enum, unique
from pathlib import Path
#from queue import Queue
from transformers import AutoTokenizer, AutoModelForCausalLM

""" 记录 Note：
让程序可以设置flags和requests的目录位置。

可以有heart_beat.flag。这样甚至可以在同一个目录下，
利用<backend_GUID>.hb.flag{datetime=xxx} -> <frontend_GUID>.<backend_GUID>.take_up.flag{datetime=xxx}来对不同的backend进行占据。
但这样没必要，不如分目录。
"""

def normalize_dir_path(path: str) -> str:
	return remove_ending_directory_separator(path)
def remove_ending_directory_separator(path: str) -> str:
	if len(path) == 0:
		return ''
	last_char = path[len(path) - 1]
	if last_char == '/' or last_char == '\\':
		return path[:-1]
	else:
		return path[::]

# 这里的常量之后应当放到字典或者类里。
__debug_dont_load_model__ = True
__api_requests_dir__ = normalize_dir_path('./requests')
__api_flags_dir__ = normalize_dir_path('./flags')
__low_cpu_mem_usage__ = True
__model_cache_dir__ = normalize_dir_path('./.cache')
__idleness_mode_threshold_time__ = 1.0
__idleness_mode_threshold_count__ = 2
__idleness_mode_sleep_time__ = 1.0

__version__ = {'major': 0, 'minor': 0, 'build': 2, 'revision': 0}
def version() -> str:
	return str(__version__['major']) + '.' + str(__version__['minor']) + '.' + str(__version__['build']) + '.' + str(__version__['revision'])

def nowtime() -> str:
	return str(datetime.now())

@unique
class Status(Enum):
	initilising = 'initilising'
	running = 'running'
	generating_text = 'generating'

class QueueList():
	def __init__(self) -> None:
		self.__recovery_threshold__ = 16
		self.__inner_list__ = []
		self.__inner_list_ptr__ = 0
			
	def contains(self, item: any) -> bool:
		return item in self.__inner_list__
	
	def __len__(self) -> int:
		return len(self.__inner_list__) - self.__inner_list_ptr__

	def add_one(self, item: any) -> None:
		self.__inner_list__.append(item)

	def get_one(self) -> any:
		print(str(self.__inner_list_ptr__))

		if len(self.__inner_list__) > 0:
			r = self.__inner_list__[self.__inner_list_ptr__]
			if self.__inner_list_ptr__ > self.__recovery_threshold__:
				self.recovery()
			else:
				self.__inner_list_ptr__ += 1
			return r
		else:
			return None
	
	def recovery(self) -> any:
		del self.__inner_list__[0, self.__inner_list_ptr__]
		self.__inner_list_ptr__ = 0

	def clear(self) -> any:
		self.__inner_list__.clear()
		self.__inner_list_ptr__ = 0



import os
 
def mkdir(path):
	if not os.path.exists(path=path):
		os.makedirs(path)

def write_all_text(path: str, text: str) -> None:
	with open(path, 'w') as file:
		file.write(text)

def read_all_text(path: str) -> str:
	r = ''
	with open(path, 'r') as file:
		while True:
			part = file.read(4096)
			if not part:
				break
			r += part
	return r

def get_files_in_dir(dir: str, end_with: str) -> list:
	r = []

	# [Solved] TypeError: listdir: path should be string, bytes, os.PathLike or None, not Namespace: https://www.solveforum.com/forums/threads/solved-typeerror-listdir-path-should-be-string-bytes-os-pathlike-or-none-not-namespace.2192804/
	# Not use above solution. Just remove the ending directory separator in the parameter like './dir/' to './dir'.
	files = os.listdir(path=dir)
	for file in files:
		if file.endswith(end_with):
			r.append(file)
	return r

def check_flags(status_values: dict) -> bool:
	flags_dir_path = Path(__api_flags_dir__)

	# Quit is a request, doesn't kill the program immediately.
	if os.path.exists(flags_dir_path / 'quit.flag'):
		print('[Info ' + nowtime() + ']: Detected quit flag ("' + str(flags_dir_path) + '/quit.flag").')
		os.remove(flags_dir_path / 'quit.flag')
		return False
	
#	if os.path.exists(flags_dir_path / 'take_down.flag"):
#		adasdasdsa
#		pass
#	
#	take_up_flags = get_files_in_dir(dit=flags_dir_path, end_with='.take_up.flag')
#	if take_up_flags.len() > 0:
#		for file in take_up_flags:
#			core_name, _ = os.path.splitext(file)
#
#			if 
#			guid = read_all_text(file)
#			if(status_values['owner_guid'].count() != ''):
#				if()

	if os.path.exists(flags_dir_path / 'status.flag'):
		print('[Info ' + nowtime() + ']: Detected query status flag ("' + str(flags_dir_path) + '/status.flag").')

		# ISO 8601: datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
		# RFC 1123: datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT') #Must use UTC!
		write_all_text(
			flags_dir_path / 'status.back',
			'DateTime: ' + datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S') + '\n' +
			'Status: ' + str(status_values['status'].name) + '\n' +
			'HandledRequestsCount: ' + str(status_values['handled_requests_count']) + '\n'
		)
		os.remove(flags_dir_path / 'status.flag')
	
	return True

def check_requests(gptj_values: dict, status_values: dict) -> bool:
	# `request_files` should be cached, diff out new request and remove disappeared request
	# that the program won't make a request be delay too much time by sorting in list.
	update_wait_queue(status_values=status_values)
	wait_queue = status_values['wait_queue']

	if len(wait_queue) > 0:
		begin_time = datetime.now()

		status_values['status'] = Status.generating_text

		file = wait_queue.get_one()
		print('[Info ' + nowtime() + ']: Handling request named "' + str(file) + '"...')
		core_name, _ = os.path.splitext(file)

		text = read_all_text(file)
		gen_text = generate_text(gptj_values = gptj_values, text = text)
		output_filename = core_name + '.back'
		print('[Info ' + nowtime() + ']: Output to "' + str(output_filename) + '".')
		write_all_text(output_filename, gen_text)
		os.remove(file)

		status_values['handled_requests_count'] += 1
		status_values['status'] = Status.running

		end_time = datetime.now()
		print('[Debug ' + nowtime() + ']: Using ' + str((end_time - begin_time).total_seconds()) + 's.')
		return True
	else:
		return False

def update_wait_queue(status_values: dict) -> None:
	wait_files = status_values['wait_queue']
	requests_dir_path = Path(__api_requests_dir__)
	request_files = get_files_in_dir(dir=__api_requests_dir__, end_with='.request')

	# For saving time, we just check and remove request file when it is popped.
	#disappeared_waiting_requests = []
	#for wait_file in wait_files:
	#	if wait_file not in request_files:
	#		disappeared_waiting_requests.append(wait_file)
	#for disappeared_waiting_request in disappeared_waiting_requests:
	#	wait_files.remove(disappeared_waiting_request)

	for request_file in request_files:
		if not wait_files.contains(Path(requests_dir_path) / request_file):
			wait_files.add_one(Path(requests_dir_path) / request_file)
			print('[Info ' + nowtime() + ']: Add request named "' + str(request_file) + '" to wait list.')
#			os.remove(request_file)

def generate_text(gptj_values: dict, text: str) -> str:
	if __debug_dont_load_model__:
		return 'debug-echo: ' + text
	
	prompt = text

	input_ids = gptj_values['tokenizer'](prompt, return_tensors="pt").input_ids

	gen_tokens = gptj_values['model'].generate(
		input_ids,
		do_sample=True,
		temperature=0.9,
		max_length=100,
	)
	gen_text = gptj_values['tokenizer'].batch_decode(gen_tokens)[0]

	return gen_text



def chatapi_gptj_main(args: list = []) -> int:
	# 暂时不检测某个flag或者request文件是否已经被另一个chatapi py后端使用。
	# 清理flags和requests应当由前端程序处理

	print('ChatAPI Backend with GPT-J-6B, Version ' + version())
	print('[Info ' + nowtime() + ']: Initlizing...')

	status_values = {}
	status_values['status'] = Status.initilising
	status_values['handled_requests_count'] = 0
	status_values['owner_guid'] = ''
	#status_values['wait_queue'] = Queue()
	status_values['wait_queue'] = QueueList() #Contains `pathlib.Path`.

	mkdir(__api_requests_dir__)
	mkdir(__api_flags_dir__)

	gptj_values = {}
	if __debug_dont_load_model__:
		print('[Debug ' + nowtime() + ']: Debug mode "don\'t load model" is on.')
		gptj_values['tokenizer'] = None
		gptj_values['model'] = None
	else:
		gptj_values['tokenizer'] = AutoTokenizer.from_pretrained(
			"EleutherAI/gpt-j-6B",
			cache_dir=__model_cache_dir__,
			resume_download=True
		)
		gptj_values['model'] = AutoModelForCausalLM.from_pretrained(
			"EleutherAI/gpt-j-6B",
			cache_dir=__model_cache_dir__,
			resume_download=True,
	#		torch_dtype=torch.float16,
			low_cpu_mem_usage=__low_cpu_mem_usage__
		)

	print('[Info ' + nowtime() + ']: Loaded.')
	print('[Info ' + nowtime() + ']: Running...')

	status_values['status'] = Status.running

	idleness_begin_time = datetime.now()
	idleness_count = 0

	while True:
		if not check_flags(status_values = status_values):
			break

		if check_requests(gptj_values = gptj_values, status_values = status_values):
			idleness_begin_time = datetime.now()
			idleness_count = 0
		else:
			if idleness_count < __idleness_mode_threshold_count__:
				idleness_count += 1
		
		# Save cpu time.
		if ((datetime.now() - idleness_begin_time).total_seconds() > __idleness_mode_threshold_time__) and (idleness_count >= __idleness_mode_threshold_count__):
			time.sleep(__idleness_mode_sleep_time__)
	
	return 0

if __name__ == '__main__':
	exit(chatapi_gptj_main())

import json
import os.path
import subprocess
import numpy as np

#save some data structure to json file
def save_json(data, filename):
	with open(filename, 'w') as fp:
		json.dump(data, fp, indent=4, sort_keys=False)
		
#load json to dictionary
def load_json(filename):
	if os.path.isfile(filename):
		with open(filename) as fp:
			data = json.load(fp)
			return data
	return False
	
#run bash command
def run_bash(command, shell=False):
	if shell:
		process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
	else:
		process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
	output, error = process.communicate()

#dump dictionary(ies) data of key->value to csv file, sorted by key
#if data is a list, each item is a dictionary, and all dictionaries have the same keys
#also pass in a list of data headers, one per column
def dump_dict_csv(data, headers, filename):
	data_keys = []
	data_vals = []

	#if list of dictionaries, handle differently
	if type(data) is list:
		data_keys = list(sorted(data[0].keys()))	#grab list of sorted keys

		#create 2D list of values
		for key in data_keys:
			row = []
			for data_dict in data:
				row.append(data_dict[key])
			data_vals.append(row)

		#combine into single np array
		data_array = np.column_stack((data_keys, data_vals))

	#one dictionary, easier
	else:
		#convert dict to lists
		for key in sorted(data.keys()):
			data_keys.append(key)
			data_vals.append(data[key])

		data_array = np.column_stack((data_keys, data_vals))

	#add headers to top of array
	data_array = np.vstack((headers, data_array))

	#save data with headers to csv
	np.savetxt(filename, data_array, delimiter=",", fmt="%s")
#end dump_dict_csv



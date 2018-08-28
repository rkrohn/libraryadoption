import json
import os.path
import subprocess
import numpy as np
import csv

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
#if data is a list, each item is a dictionary, and all dictionaries have the same keys, 
#write key column once and all value columns following
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

#given a dictionary of key->list of values, output the data to csv
#first column is keys, rest of row is values associated with that key
def dump_dict_of_lists(data, headers, filename):
    with open(filename, 'w') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(headers)
        for key in sorted(data.keys()):
        	writer.writerow([key] + data[key])
#end dump_dict_of_lists

#given a list of lists, output data to csv, one list per row
#headers in this case refer to the labels placed at the start of each row
def dump_lists(data, headers, filename):
	with open(filename, 'w') as file:
		writer = csv.writer(file, delimiter=',')
		for i in range(len(headers)):
			writer.writerow([headers[i]] + data[i])
#end dump_lists

#given a list and associated headers, dump to csv
def dump_list(data, headers, filename):
	with open(filename, "w") as f:
		writer = csv.writer(f)
		writer.writerow(headers)
		writer.writerows(data)
#end dump_list



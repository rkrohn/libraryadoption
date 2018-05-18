#computes and plots user and repo commit frequencies, creating user list along the way

import json
import os.path
import subprocess
import sys
import urllib2
import io
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pylab as plt
import numpy as np
import unicodedata

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

#given dictionary of form key->count, compute frequencies of different counts
def count_freq(data):
	freq = defaultdict(int)
	min = -1
	max = -1
	for key in data:
		freq[data[key]] = freq[data[key]] + 1
		if min == -1 or data[key] < min:
			min = data[key]
		if max == -1 or data[key] > max:
			max = data[key]
	return freq, min, max
		
	
#given frequencies as dictionary, key = size, value = freq, plot them	
def plot_freq(freq, xlabel, ylabel, filename = "", x_max = 0):	
	lists = sorted(freq.items())
	x,y = zip(*lists)
	plt.plot(x,y)
	plt.xlabel(xlabel)
	plt.ylabel(ylabel)
	if x_max != 0:
		plt.xlim(xmin=0, xmax=x_max)
	if filename == "":
		plt.show()
	else:
		plt.savefig(filename, bbox_inches='tight')

#--- MAIN EXECUTION BEGINS HERE---#	

#read mappings from files
email_to_id = load_json("email_to_userid.json")
name_to_id = load_json("name_to_userid.json")

user_commit_counts = load_json("user_commit_counts.json")
if user_commit_counts == False:
	user_commit_counts = defaultdict(int)
file_commit_counts = load_json("file_commit_counts.json")
if file_commit_counts == False:
	file_commit_counts = defaultdict(int)

file_idx = 0

if len(file_commit_counts) == 0 or len(user_commit_counts) == 0:
	print "computing counts"
	#for each commit log file:
	for filename in os.listdir('commit_data'):
		imports = False
		#open file, process lines one at a time
		for line in io.open("commit_data/%s" % filename, encoding="ISO-8859-1"):
			#commit line
			if line.startswith("#######"):
				#count previous commit if had import
				if imports:
					user_commit_counts[user_id] = user_commit_counts[user_id] + 1
					file_commit_counts[filename] = file_commit_counts[filename] + 1
					imports = False	

				#extract commit metadata for "new" commit
				line = line.replace("#######", "")
				commit = [x.strip() for x in line.split(',')]	#email, name, UTC
				#check for diff lines that happen to start with commit flag
				if len(commit) != 3:
					continue
				email = commit[0]
				name = commit[1]
				name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore')
				
				#mystery committer, just skip and move on
				if name == "" and email == "":
					continue
				#otherwise, get user id for this user
				if name != "":
					user_id = name_to_id[name]
				else:
					user_id = email_to_id[email]
		
			#diff line
			else:
				imports = True
				
		file_idx = file_idx + 1
		if file_idx % 1000 == 0:
			print "finished", file_idx, "files"
			
	print "COMPLETE"

	#save results	
	save_json(user_commit_counts, "user_commit_counts.json")
	save_json(file_commit_counts, "file_commit_counts.json")
	print "final user list saved to user_commit_counts.json and file_commit_counts.json"
else:
	print "counts already computed, plotting frequencies"
	
	#user commit plots
	user_commit_freq, min_user_commit, max_user_commit = count_freq(user_commit_counts)
	plot_freq(user_commit_freq, "user commit count", "freq", filename = "user_commit_freq.jpg")
	print "user commit counts: min =", min_user_commit, ", max =", max_user_commit
	
	#repo commit plots
	repo_commit_freq, min_repo_commit, max_repo_commit = count_freq(file_commit_counts)
	plot_freq(repo_commit_freq, "repo commit count", "freq", filename = "repo_commit_freq.jpg")
	print "user commit counts: min =", min_repo_commit, ", max =", max_repo_commit
	
	print "plots saved to user_commit_freq.jpg and repo_commit_freq.jpg"
	



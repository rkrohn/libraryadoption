#compile and plot user and repo commit frequencies

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
import file_utils as utils
import plot_utils

#--- MAIN EXECUTION BEGINS HERE---#	

#read mappings from files
email_to_id = utils.load_json("email_to_userid.json")
name_to_id = utils.load_json("name_to_userid.json")

user_commit_counts = utils.load_json("user_commit_counts.json")
if user_commit_counts == False:
	user_commit_counts = defaultdict(int)
file_commit_counts = utils.load_json("file_commit_counts.json")
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
	utils.save_json(user_commit_counts, "user_commit_counts.json")
	utils.save_json(file_commit_counts, "file_commit_counts.json")
	print "final user list saved to user_commit_counts.json and file_commit_counts.json"
else:
	print "counts already computed, plotting frequencies"
	
	#user commit plots
	user_commit_freq, min_user_commit, max_user_commit = plot_utils.count_freq(user_commit_counts)
	plot_utils.plot_freq(user_commit_freq, "user commit count", "freq", filename = "user_commit_freq.jpg")
	print "user commit counts: min =", min_user_commit, ", max =", max_user_commit
	
	#repo commit plots
	repo_commit_freq, min_repo_commit, max_repo_commit = plot_utils.count_freq(file_commit_counts)
	plot_utils.plot_freq(repo_commit_freq, "repo commit count", "freq", filename = "repo_commit_freq.jpg")
	print "user commit counts: min =", min_repo_commit, ", max =", max_repo_commit
	
	print "plots saved to user_commit_freq.jpg and repo_commit_freq.jpg"
	



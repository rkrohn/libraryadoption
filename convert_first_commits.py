#convert raw first commit data to better-formatted dictionary

import json
import os.path
import subprocess
import sys
import urllib2
import io
import unicodedata
from collections import defaultdict

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

#--- MAIN EXECUTION BEGINS HERE---#	

#read first_commits
raw_commits = load_json("datafiles/first_commits_RAW.json")

#new data structure, list of commits as dictionaries, all integer values
commits = list()
missing_time_count = 0

#loop users
for user in raw_commits:
	#loop commits, each a list containing repo and timestamp
	for commit in raw_commits[user]:
		time = commit[1]
		repo = commit[0]
		
		#verify that commit has valid timestamp
		if len(time) == 0:
			missing_time_count = missing_time_count + 1
			continue
			
		new_commit = {}
		new_commit["user"] = int(user)
		new_commit["repo"] = repo
		new_commit["time"] = int(time)	
		
		commits.append(new_commit)

#save results
#save updated user lists
save_json(commits, "datafiles/first_commits.json")
print "formatted commit list saved to datafiles/first_commits.json"
print "   ", len(commits), "user first commits"
print "   ", missing_time_count, "commits without timestamps"
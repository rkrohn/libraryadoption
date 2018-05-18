#legacy code, shouldn't need this anymore - searches list of repos for duplicate names

import json
import os.path
import subprocess
import sys

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
	
#--- MAIN EXECUTION BEGINS HERE---#	

#read list of repos to check
repos = load_json("all_repos.json")
print "Read", len(repos['items']), "repos"

#keep list of repo names, since apparently they aren't all unique
name_list = list()

#also keep shorter list of previously discovered duplicates
duplicates = load_json("duplicate_names.json")
if duplicates == False:
	duplicates = list()
	
for r in repos['items']:
	repo_name = r['name']
	
	#already registered as duplicate, continue
	if repo_name in duplicates:
		continue
		
	#first duplicate with this name, add to offenders list	
	elif repo_name in name_list:
		duplicates.append(repo_name)
		
	#unique name, add to list	
	else:
		name_list.append(repo_name)
	
#save list of duplicate-name repos to json file
save_json(duplicates, "duplicate_names.json")
#legacy code, shouldn't need this anymore - searches list of repos for duplicate names

import file_utils as utils
	
#--- MAIN EXECUTION BEGINS HERE---#	

#read list of repos to check
repos = utils.load_json("all_repos.json")
print "Read", len(repos['items']), "repos"

#keep list of repo names, since apparently they aren't all unique
name_list = list()

#also keep shorter list of previously discovered duplicates
duplicates = utils.load_json("duplicate_names.json")
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
#utils.save_json(duplicates, "duplicate_names.json")